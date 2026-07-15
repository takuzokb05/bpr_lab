# Analysis of Claude Code codebase: 500,000 lines total, only 1.6% is AI model c

- URL: https://x.com/jackvi810/status/2066764688210436240
- ソース: x
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-18
- いいね: 5 / RT: 0 / リプライ: 0
- 投稿者: @jackvi810 / フォロワー 31,444

## 投稿内容

Claude Code có 500.000 dòng code, nhưng chỉ 1,6% thực sự là AI

Trong suốt hai năm qua, cả ngành AI gần như bị ám ảnh bởi một ý tưởng rất đơn giản: muốn tạo ra sản phẩm AI tốt hơn thì phải có model mạnh hơn. Nhiều tham số hơn, nhiều GPU hơn, nhiều dữ liệu hơn, nhiều benchmark hơn. 

Điều đó khiến rất nhiều người vô thức tin rằng phần quan trọng nhất của một AI agent nằm ở chính model. Nhưng một nghiên cứu gần đây về Claude Code lại cho thấy một sự thật khá thú vị. Có lẽ chúng ta đã nhìn nhầm chỗ.

Sau khi khoảng 500.000 dòng code TypeScript của Claude Code xuất hiện trên Internet, một nhóm nghiên cứu từ MBZUAI và University College London đã tiến hành phân tích toàn bộ hệ thống. Điều họ phát hiện ra khá bất ngờ. Chỉ khoảng 1,6% codebase liên quan trực tiếp đến việc gọi model và xử lý suy luận của AI. 98,4% còn lại là phần mềm truyền thống.

Nghe qua thì điều này có vẻ khó tin. Nhưng nếu nhìn kỹ hơn, nó lại hoàn toàn hợp lý. Bởi vì vấn đề lớn nhất của AI hiện đại không còn là làm cho nó thông minh hơn. Vấn đề thực sự nằm ở việc làm sao để quản lý được sự thông minh đó.

Nếu bóc tách Claude Code xuống mức cơ bản nhất, phần lõi của nó thực sự rất đơn giản. Nhóm nghiên cứu mô tả trái tim của cả hệ thống chỉ là một vòng lặp mang tên `queryLoop()`. Quy trình hoạt động gần như chỉ gồm ba bước: hỏi model nên làm gì tiếp theo, thực thi công cụ tương ứng, sau đó đưa kết quả trở lại cho model và tiếp tục lặp lại. Nói cách khác, phần "AI" thực chất chỉ là một vòng while rất đơn giản. Điều phức tạp nằm ở mọi thứ xung quanh vòng lặp đó.

Nếu coi Claude là một thực tập sinh cực kỳ thông minh, thì 98% code còn lại tồn tại để đóng vai người quản lý. Bởi vì thực tập sinh này tuy giỏi nhưng cũng có rất nhiều vấn đề. Nó có thể quên mục tiêu ban đầu. Nó có thể hiểu sai yêu cầu. Nó có thể tự ý sửa nhầm file. Nó có thể bị mắc kẹt trong một vòng lặp vô tận. Nó có thể tưởng tượng ra những thứ không tồn tại. Và trong trường hợp xấu nhất, nó có thể phá hỏng cả dự án của người dùng.

Chính vì vậy, phần lớn kỹ thuật bên trong Claude Code không phải machine learning. Nó là kỹ thuật phần mềm truyền thống theo đúng nghĩa. Nhóm nghiên cứu phát hiện hệ thống được chia thành bảy thành phần lớn bao gồm giao diện người dùng, agent loop, hệ thống quyền, tập hợp công cụ, quản lý trạng thái, môi trường thực thi và lớp tương tác với người dùng. Phần lớn những thứ này không khác nhiều so với những gì các kỹ sư backend và hạ tầng đã xây dựng suốt hàng chục năm qua.

Một phát hiện thú vị khác là Anthropic dường như không hề tin tưởng hoàn toàn vào chính model của mình. Claude Code được xây dựng với bảy lớp bảo vệ độc lập. Chỉ cần một lớp phát hiện rủi ro, hành động sẽ bị chặn lại. Có những lớp loại bỏ trước các công cụ nguy hiểm, các quy tắc từ chối mặc định, bộ phân loại bằng machine learning, sandbox cho shell command và các hook kiểm tra trước khi hành động được thực thi. 

Điều này cho thấy Anthropic không coi Claude như một cỗ máy hoàn hảo. Họ coi nó giống như một nhân viên rất giỏi nhưng vẫn cần có hàng rào bảo vệ xung quanh.

Một trong những bài toán lớn nhất mà Claude Code phải giải quyết lại không liên quan đến GPU hay tốc độ suy luận. Đó là trí nhớ. Mặc dù Claude 4.6 có thể xử lý tới một triệu token, Anthropic vẫn phải xây dựng một pipeline nén ngữ cảnh gồm năm tầng khác nhau để giữ cho agent không quên mục tiêu ban đầu. 

Các cơ chế như budget reduction, microcompact hay auto-compact liên tục hoạt động phía sau để giảm lượng token mà model phải ghi nhớ. Điều này tiết lộ một sự thật thú vị: ngay cả một triệu token vẫn chưa phải là vô hạn. Context vẫn là tài nguyên khan hiếm nhất của AI.

Nhóm nghiên cứu cũng phát hiện Claude Code có thể sử dụng tới 54 công cụ khác nhau, trong đó có 19 công cụ luôn tồn tại và 35 công cụ được kích hoạt tùy thuộc vào cấu hình và feature flag. Ngoài ra còn có các MCP server, hook, plugin và skill để mở rộng năng lực của hệ thống. Điều này cho thấy AI agent thực chất không phải là một model đơn lẻ. Nó là cả một hệ sinh thái công cụ bao quanh model.

Có lẽ phát hiện thú vị nhất trong toàn bộ nghiên cứu nằm ở triết lý thiết kế của Anthropic. Các tác giả mô tả Claude Code bằng cụm từ "minimal scaffolding, maximal operational harness". Tạm dịch là giảm tối đa phần điều phối thông minh, tăng tối đa hạ tầng vận hành. Thay vì xây dựng những planner phức tạp hay state machine cứng nhắc, Anthropic để model tự suy nghĩ. Còn phần mềm truyền thống sẽ chịu trách nhiệm quản lý môi trường xung quanh.

Điều này hoàn toàn đi ngược với trực giác của phần lớn ngành AI hiện nay. Trong khi mọi người vẫn đang cố gắng làm cho model ngày càng thông minh hơn, Anthropic dường như đã đi đến một kết luận khác. Có thể AI không cần phải thông minh hơn quá nhiều nữa. Điều nó thực sự cần là được quản lý tốt hơn.

Nhìn từ góc độ đó, Claude Code không giống một chatbot. Nó cũng không giống một mô hình ngôn ngữ đơn thuần. Nó giống một hệ điều hành dành cho AI hơn. Model chỉ là CPU. Còn 98% phần còn lại mới là bộ nhớ, hệ thống tập tin, trình quản lý tiến trình, cơ chế phân quyền và toàn bộ lớp hạ tầng giúp cỗ máy đó vận hành ổn định.

Có lẽ đây mới là insight quan trọng nhất mà nghiên cứu này mang lại. Lợi thế cạnh tranh của AI trong tương lai có thể không nằm ở bộ não. Bộ não đang dần trở thành hàng hóa. Thứ khó xây dựng hơn nhiều nằm ở hệ thần kinh bao quanh bộ não đó. Và dường như Anthropic đã nhận ra điều này sớm hơn phần còn lại của ngành.

Anh em mê AI thì đừng quên join group @nghienaivn ở đây nha 👇
https://t.co/wOX7GsW3qv

## 要約

Analysis of Claude Code codebase: 500,000 lines total, only 1.6% is AI model code — insight into Claude Code's architecture and engineering emphasis。
投稿者 @jackvi810（フォロワー31,444人）によるclaude-ecosystem関連情報。
投稿内容の要点: Claude Code có 500.000 dòng code, nhưng chỉ 1,6% thực sự là AI
