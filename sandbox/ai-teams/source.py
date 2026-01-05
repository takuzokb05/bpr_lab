from openai import OpenAI

# 譁ｰ縺励＞API繧ｭ繝ｼ縺ｧ遒ｺ隱・
OPENAI_API_KEY = "REMOVED_SECRET"

print("=" * 60)
print("､・OpenAI 繝｢繝・Ν遒ｺ隱・)
print("=" * 60)

try:
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    print("\n搭 蛻ｩ逕ｨ蜿ｯ閭ｽ縺ｪ繝｢繝・Ν繧貞叙蠕嶺ｸｭ...\n")
    models = client.models.list()
    
    # GPT繝｢繝・Ν縺ｮ縺ｿ繝輔ぅ繝ｫ繧ｿ繝ｪ繝ｳ繧ｰ
    gpt_models = sorted([m.id for m in models.data if m.id.startswith("gpt")], reverse=True)
    
    # 繧ｫ繝・ざ繝ｪ蛻･縺ｫ蛻・｡・
    gpt_4o_models = [m for m in gpt_models if "gpt-4o" in m]
    gpt_4_models = [m for m in gpt_models if m.startswith("gpt-4") and "gpt-4o" not in m]
    gpt_3_models = [m for m in gpt_models if m.startswith("gpt-3")]
    
    print("検 GPT-4o 繧ｷ繝ｪ繝ｼ繧ｺ (譛譁ｰ繝ｻ謗ｨ螂ｨ):")
    for m in gpt_4o_models[:10]:
        print(f"  笨・{m}")
    
    print(f"\n箝・GPT-4 繧ｷ繝ｪ繝ｼ繧ｺ:")
    for m in gpt_4_models[:5]:
        print(f"  笨・{m}")
    
    print(f"\n逃 GPT-3.5 繧ｷ繝ｪ繝ｼ繧ｺ:")
    for m in gpt_3_models[:5]:
        print(f"  笨・{m}")
    
    print(f"\n笨・蜷郁ｨ・{len(gpt_models)} GPT繝｢繝・Ν蛻ｩ逕ｨ蜿ｯ閭ｽ")
    
    # 謗ｨ螂ｨ繝｢繝・Ν
    print("\n" + "=" * 60)
    print("庁 謗ｨ螂ｨ繝｢繝・Ν:")
    print("=" * 60)
    
    recommended = [m for m in gpt_4o_models if m in ["gpt-4o", "gpt-4o-mini", "gpt-4o-2024-11-20"]]
    if recommended:
        for m in recommended:
            print(f"  識 {m}")
    else:
        print("  識 gpt-4o (譛譁ｰ)")
        print("  識 gpt-4o-mini (繧ｳ繧ｹ繝亥柑邇・")
    
except Exception as e:
    print(f"笶・繧ｨ繝ｩ繝ｼ: {e}")
    print("\n隧ｳ邏ｰ:")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
