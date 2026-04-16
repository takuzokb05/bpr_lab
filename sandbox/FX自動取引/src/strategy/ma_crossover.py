"""
RSIフィルター + ADXフィルター + MFIフィルター付き移動平均クロスオーバー戦略

MA(短期)とMA(長期)のクロスオーバーに基づくシグナル生成を行い、
RSIフィルターで買われすぎ/売られすぎ局面でのエントリーを排除し、
ADXフィルターでトレンドが弱い局面でのエントリーを排除し、
MFIフィルター（price+volume）で買われすぎ/売られすぎを排除する。
損切りはATRベース、利確はリスクリワード比に基づく。

doc 04 セクション5.1 準拠。Phase 2 F15 ADXフィルター追加。Phase 3 MFIフィルター追加。
"""

import logging
from typing import Optional

import pandas as pd
import pandas_ta as ta

from src.config import (
    ADX_PERIOD,
    ADX_THRESHOLD,
    ATR_MULTIPLIER,
    ATR_PERIOD,
    MA_LONG_PERIOD,
    MA_SHORT_PERIOD,
    MFI_ENABLED,
    MFI_OVERBOUGHT,
    MFI_OVERSOLD,
    MFI_PERIOD,
    MIN_RISK_REWARD,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    RSI_PERIOD,
)
from src.strategy.base import Signal, StrategyBase

logger = logging.getLogger(__name__)


class RsiMaCrossover(StrategyBase):
    """
    RSIフィルター + ADXフィルター + MFIフィルター付きMA（移動平均）クロスオーバー戦略

    エントリー条件:
    - ADX >= ADX_THRESHOLD（トレンドが十分に強い）
    - MFI_ENABLED時: MFIによる買われすぎ/売られすぎフィルタ
    - 買い: MA短期がMA長期を上抜け かつ RSI < RSI_OVERBOUGHT かつ MFI < MFI_OVERBOUGHT
    - 売り: MA短期がMA長期を下抜け かつ RSI > RSI_OVERSOLD かつ MFI > MFI_OVERSOLD
    - それ以外: HOLD

    診断情報:
    - generate_signal() 実行後に last_diagnostics プロパティで取得可能

    損切り: ATRベース（ATR * ATR_MULTIPLIER）
    利確: リスクリワード比 MIN_RISK_REWARD 以上
    """

    def __init__(self) -> None:
        # 直近のgenerate_signal()実行時の診断情報
        self._diagnostics: Optional[dict] = None

    @property
    def last_diagnostics(self) -> Optional[dict]:
        """直近のgenerate_signal()実行時の診断情報を返す。"""
        return self._diagnostics

    def generate_signal(self, data: pd.DataFrame, **kwargs) -> Signal:
        """
        MA クロスオーバーとRSIフィルターに基づくシグナルを生成する。

        Args:
            data: OHLCV形式のDataFrame（close列が必須、RSI計算にはhigh/low/close列を推奨）
            **kwargs: indicators（IndicatorCache辞書）等の追加パラメータ

        Returns:
            Signal: BUY / SELL / HOLD
        """
        # IndicatorCacheからの指標取得（キャッシュがあればpandas_ta計算をスキップ）
        indicators = kwargs.get("indicators")

        # データ行数がMA長期期間未満なら計算不能 → HOLD
        if len(data) < MA_LONG_PERIOD:
            logger.warning(
                "データ行数が不足しています（%d行 < %d行）。HOLDを返します。",
                len(data),
                MA_LONG_PERIOD,
            )
            return Signal.HOLD

        # 移動平均の計算（キャッシュ優先）
        if indicators is not None and indicators.get("ma_short") is not None:
            ma_short = indicators["ma_short"]
        else:
            ma_short = ta.sma(data["close"], length=MA_SHORT_PERIOD)

        if indicators is not None and indicators.get("ma_long") is not None:
            ma_long = indicators["ma_long"]
        else:
            ma_long = ta.sma(data["close"], length=MA_LONG_PERIOD)

        # RSIの計算（キャッシュ優先）
        if indicators is not None and indicators.get("rsi") is not None:
            rsi = indicators["rsi"]
        else:
            rsi = ta.rsi(data["close"], length=RSI_PERIOD)

        # いずれかの指標がNoneの場合はHOLD
        if ma_short is None or ma_long is None or rsi is None:
            logger.warning("テクニカル指標の計算に失敗しました。HOLDを返します。")
            return Signal.HOLD

        # 現在バーと前バーの値を取得
        current_ma_short = ma_short.iloc[-1]
        current_ma_long = ma_long.iloc[-1]
        prev_ma_short = ma_short.iloc[-2]
        prev_ma_long = ma_long.iloc[-2]
        current_rsi = rsi.iloc[-1]

        # NaN チェック（MA長期の初期値はNaNになる）
        if pd.isna(current_ma_short) or pd.isna(current_ma_long) or pd.isna(current_rsi):
            logger.warning(
                "テクニカル指標にNaN値が含まれています。HOLDを返します。"
            )
            return Signal.HOLD

        if pd.isna(prev_ma_short) or pd.isna(prev_ma_long):
            logger.warning(
                "前バーのMA値にNaNが含まれています。HOLDを返します。"
            )
            return Signal.HOLD

        # ADXフィルター: トレンドの強さを判定（F15追加）
        # キャッシュからcurrent_adxを取得、またはpandas_taで計算
        if indicators is not None and indicators.get("current_adx") is not None:
            current_adx = indicators["current_adx"]
        else:
            adx_df = ta.adx(data["high"], data["low"], data["close"], length=ADX_PERIOD)
            if adx_df is None:
                logger.warning("ADX計算に失敗しました。HOLDを返します。")
                return Signal.HOLD

            adx_col = f"ADX_{ADX_PERIOD}"
            if adx_col not in adx_df.columns:
                logger.warning("ADX列が見つかりません: %s。HOLDを返します。", adx_col)
                return Signal.HOLD

            current_adx = adx_df[adx_col].iloc[-1]

        if pd.isna(current_adx):
            logger.warning("ADX値がNaNです。HOLDを返します。")
            return Signal.HOLD

        # MFIフィルター: price + volume ベースの買われすぎ/売られすぎ判定（Phase 3 追加）
        # キャッシュからcurrent_mfiを取得、またはpandas_taで計算
        current_mfi = None
        mfi_available = False
        if indicators is not None and indicators.get("current_mfi") is not None:
            current_mfi = indicators["current_mfi"]
            mfi_available = True
        elif MFI_ENABLED:
            vol_col = None
            if "volume" in data.columns:
                vol_col = "volume"
            elif "tick_volume" in data.columns:
                vol_col = "tick_volume"

            if vol_col is not None:
                mfi_series = ta.mfi(
                    data["high"], data["low"], data["close"], data[vol_col],
                    length=MFI_PERIOD,
                )
                if mfi_series is not None and not pd.isna(mfi_series.iloc[-1]):
                    current_mfi = float(mfi_series.iloc[-1])
                    mfi_available = True
                else:
                    logger.debug("MFI計算結果がNaN。MFIフィルターをスキップします。")
            else:
                logger.debug("volume/tick_volume列なし。MFIフィルターをスキップします。")

        # 診断ログ: 全指標の現在値を出力
        ma_diff = current_ma_short - current_ma_long
        ma_position = "短期>長期" if current_ma_short > current_ma_long else "短期<長期"
        crossover = "なし"
        if prev_ma_short <= prev_ma_long and current_ma_short > current_ma_long:
            crossover = "上抜け(BUY候補)"
        elif prev_ma_short >= prev_ma_long and current_ma_short < current_ma_long:
            crossover = "下抜け(SELL候補)"

        mfi_log = f" MFI={current_mfi:.1f}" if mfi_available else " MFI=N/A"
        logger.debug(
            "指標診断: MA短=%.3f MA長=%.3f 差=%.3f(%s) "
            "クロス=%s RSI=%.1f ADX=%.1f(閾値%.1f)%s",
            current_ma_short,
            current_ma_long,
            ma_diff,
            ma_position,
            crossover,
            current_rsi,
            current_adx,
            ADX_THRESHOLD,
            mfi_log,
        )

        # 診断情報を格納（コンソールサマリー用）
        diag: dict = {
            "ma_diff": float(ma_diff),
            "ma_position": ma_position,
            "crossover": crossover,
            "rsi": float(current_rsi),
            "adx": float(current_adx),
            "adx_threshold": ADX_THRESHOLD,
            "mfi": current_mfi,
            "mfi_filter": "有効" if mfi_available else ("無効" if not MFI_ENABLED else "データなし"),
        }

        if current_adx < ADX_THRESHOLD:
            diag["hold_reason"] = f"ADX弱({current_adx:.1f}<{ADX_THRESHOLD:.0f})"
            self._diagnostics = diag
            logger.debug(
                "→ HOLD理由: ADXフィルター（ADX=%.1f < 閾値%.1f、トレンド弱）",
                current_adx,
                ADX_THRESHOLD,
            )
            return Signal.HOLD

        # 買いシグナル: MA短期がMA長期を上抜け かつ RSI < 買われすぎ閾値
        if (
            prev_ma_short <= prev_ma_long
            and current_ma_short > current_ma_long
            and current_rsi < RSI_OVERBOUGHT
        ):
            # MFIフィルター: 買われすぎなら見送り
            if mfi_available and current_mfi >= MFI_OVERBOUGHT:
                diag["hold_reason"] = f"MFI買われすぎ({current_mfi:.1f}>={MFI_OVERBOUGHT})"
                self._diagnostics = diag
                logger.debug(
                    "→ HOLD理由: MFIフィルター（MFI=%.1f >= 閾値%d、買われすぎ）",
                    current_mfi,
                    MFI_OVERBOUGHT,
                )
                return Signal.HOLD

            diag["hold_reason"] = None
            self._diagnostics = diag
            mfi_info = f", MFI={current_mfi:.1f}" if mfi_available else ""
            logger.info(
                "買いシグナル検出: MA短期(%.5f) > MA長期(%.5f), RSI=%.2f, ADX=%.1f%s",
                current_ma_short,
                current_ma_long,
                current_rsi,
                current_adx,
                mfi_info,
            )
            return Signal.BUY

        # 売りシグナル: MA短期がMA長期を下抜け かつ RSI > 売られすぎ閾値
        if (
            prev_ma_short >= prev_ma_long
            and current_ma_short < current_ma_long
            and current_rsi > RSI_OVERSOLD
        ):
            # MFIフィルター: 売られすぎなら見送り
            if mfi_available and current_mfi <= MFI_OVERSOLD:
                diag["hold_reason"] = f"MFI売られすぎ({current_mfi:.1f}<={MFI_OVERSOLD})"
                self._diagnostics = diag
                logger.debug(
                    "→ HOLD理由: MFIフィルター（MFI=%.1f <= 閾値%d、売られすぎ）",
                    current_mfi,
                    MFI_OVERSOLD,
                )
                return Signal.HOLD

            diag["hold_reason"] = None
            self._diagnostics = diag
            mfi_info = f", MFI={current_mfi:.1f}" if mfi_available else ""
            logger.info(
                "売りシグナル検出: MA短期(%.5f) < MA長期(%.5f), RSI=%.2f, ADX=%.1f%s",
                current_ma_short,
                current_ma_long,
                current_rsi,
                current_adx,
                mfi_info,
            )
            return Signal.SELL

        # クロスオーバーが発生していない（MAが既に片側に安定）
        diag["hold_reason"] = f"クロス待ち(差{abs(ma_diff):.3f})"
        self._diagnostics = diag
        logger.debug(
            "→ HOLD理由: クロスオーバー未発生（%s、差=%.3f）",
            ma_position,
            abs(ma_diff),
        )
        return Signal.HOLD

    def calculate_stop_loss(
        self, entry_price: float, direction: str, data: pd.DataFrame
    ) -> float:
        """
        ATRベースの損切り価格を算出する。

        Args:
            entry_price: エントリー価格
            direction: "BUY" または "SELL"
            data: OHLCV形式のDataFrame（high, low, close列が必要）

        Returns:
            損切り価格

        Raises:
            ValueError: ATR計算不能（データ不足）時。
                        呼び出し側でエントリーを見送ること（HOLD扱い）。
            ValueError: direction が 'BUY' でも 'SELL' でもない場合。
        """
        # ATRの計算
        atr = ta.atr(data["high"], data["low"], data["close"], length=ATR_PERIOD)

        # ATR計算不能（データ不足やNaN）→ ValueError送出（H1: 安全側に倒す）
        # 呼び出し元でエントリーを見送る（HOLD扱い）べき
        if atr is None or pd.isna(atr.iloc[-1]):
            raise ValueError(
                f"ATR計算不能: データ不足のため損切り価格を算出できません "
                f"(entry_price={entry_price})"
            )

        current_atr = atr.iloc[-1]

        if direction == "BUY":
            stop_loss = entry_price - current_atr * ATR_MULTIPLIER
        elif direction == "SELL":
            stop_loss = entry_price + current_atr * ATR_MULTIPLIER
        else:
            raise ValueError(
                f"directionは 'BUY' または 'SELL' である必要があります: '{direction}'"
            )

        logger.info(
            "損切り価格算出: direction=%s, entry=%.5f, ATR=%.5f, SL=%.5f",
            direction,
            entry_price,
            current_atr,
            stop_loss,
        )
        return stop_loss

    def calculate_take_profit(
        self, entry_price: float, direction: str, stop_loss: float
    ) -> float:
        """
        リスクリワード比に基づく利確価格を算出する。

        リスク（エントリー価格と損切り価格の差分）に対して
        MIN_RISK_REWARD倍のリワードを確保する利確価格を算出する。

        Args:
            entry_price: エントリー価格
            direction: "BUY" または "SELL"
            stop_loss: 損切り価格

        Returns:
            利確価格

        Raises:
            ValueError: 損切り幅がゼロ（entry_price == stop_loss）の場合。
            ValueError: direction が 'BUY' でも 'SELL' でもない場合。
        """
        risk = abs(entry_price - stop_loss)

        # risk=0（SL=entry_price）は損切り幅ゼロの危険な注文になる
        if risk == 0:
            raise ValueError(
                "損切り幅がゼロのため利確価格を算出できません "
                f"(entry_price={entry_price}, stop_loss={stop_loss})"
            )

        if direction == "BUY":
            take_profit = entry_price + risk * MIN_RISK_REWARD
        elif direction == "SELL":
            take_profit = entry_price - risk * MIN_RISK_REWARD
        else:
            raise ValueError(
                f"directionは 'BUY' または 'SELL' である必要があります: '{direction}'"
            )

        logger.info(
            "利確価格算出: direction=%s, entry=%.5f, SL=%.5f, risk=%.5f, TP=%.5f",
            direction,
            entry_price,
            stop_loss,
            risk,
            take_profit,
        )
        return take_profit
