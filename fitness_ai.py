import streamlit as st
import requests
import os

# ==================== 配置 ====================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "0014e00356a746668dc44b10f3ef8102.QhgDIgIbMASeCQOw")
ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "glm-4.7")

# 页面配置
st.set_page_config(
    page_title="AI健身助手",
    page_icon="💪",
    layout="wide"
)

# ==================== CSS 样式 ====================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px 0;
    }
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .plan-card {
        background: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #667eea;
    }
    .main-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        text-align: center;
        color: gray;
        font-size: 0.8em;
        padding: 15px 0;
        background: white;
        border-top: 1px solid #eee;
        z-index: 999;
    }
    /* 为内容区域添加底部内边距，避免被页脚遮挡 */
    .main .block-container {
        padding-bottom: 70px;
    }
    /* 调整聊天输入框位置，避免与页脚重叠 */
    .stChatInput {
        padding-bottom: 70px;
    }
    /* 隐藏聊天消息上方的横线 */
    .stChatMessage {
        border-top: none !important;
    }
    /* 隐藏聊天输入框上方的横线 */
    [data-testid="stChatInput"] hr {
        display: none !important;
    }
    .st-emotion-cache-1s8qyds hr {
        display: none !important;
    }
    [data-testid="stChatInput"] + hr {
        display: none !important;
    }
    .stChatInput hr,
    .stChatInputContainer hr {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 系统提示词 ====================
SYSTEM_PROMPT = """
你是一位专业持证的健身私教，拥有10年以上的健身指导经验。

你的职责：
1. 根据用户的基本信息（性别、年龄、身高、体重、健身目标）制定个性化训练计划
2. 讲解动作标准、发力方式、避免受伤
3. 提供饮食营养建议，包括减脂/增肌的饮食方案
4. 回答健身相关问题
5. 提醒运动安全，绝不提供危险动作

回答风格：
- 专业、简洁、可执行
- 使用emoji增强可读性
- 将训练计划结构化展示（用标题、列表、表格）
- 计划应具体到每周训练天数、每次训练内容、组数、次数
- 每次回答后询问用户是否需要调整或补充

注意：
- 绝不回答健身以外的内容
- 严格保持行业AI定位
- 根据用户BMI和目标给出合理建议
"""

# ==================== 会话状态初始化 ====================
if "page" not in st.session_state:
    st.session_state.page = "chat"
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "plan_generated" not in st.session_state:
    st.session_state.plan_generated = False

# ==================== 侧边栏导航 ====================
with st.sidebar:
    st.title("💪 AI健身助手")
    st.markdown("---")

    if st.button("📋 我的信息"):
        st.session_state.page = "info"
    if st.button("🏋️ 我的计划"):
        st.session_state.page = "plan"
    if st.button("💬 咨询教练"):
        st.session_state.page = "chat"
    if st.button("🔄 重置所有"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("---")
    if st.session_state.user_info:
        st.info("👤 已录入用户信息")
    if st.session_state.plan_generated:
        st.success("📝 已生成训练计划")

# ==================== 调用 Anthropic Claude API ====================
def call_claude_api(messages):
    try:
        # 将 messages 转换为 Claude 格式
        system_prompt = ""
        claude_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                claude_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                claude_messages.append({"role": "assistant", "content": msg["content"]})

        payload = {
            "model": ANTHROPIC_MODEL,
            "messages": claude_messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }

        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        response = requests.post(f"{ANTHROPIC_BASE_URL}/v1/messages", json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        result = response.json()

        if "content" in result and len(result["content"]) > 0:
            return result["content"][0]["text"]
        else:
            return "抱歉，AI返回的格式有误，请稍后重试。"

    except requests.exceptions.Timeout:
        return "请求超时，请检查网络连接后重试。"
    except requests.exceptions.ConnectionError:
        return "网络连接失败，请检查您的网络设置。"
    except requests.exceptions.HTTPError as e:
        return f"API请求失败 (HTTP {response.status_code}): {str(e)}"
    except Exception as e:
        return f"发生未知错误: {str(e)}"

# ==================== 计算BMI ====================
def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 1)

# ==================== 主页面逻辑 ====================

# ========== 页面1: 信息录入 ==========
if st.session_state.page == "info":
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("📋 完善您的信息")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("请填写以下信息，我将为您量身定制健身计划：")

    with st.form("user_info_form"):
        col1, col2 = st.columns(2)

        with col1:
            gender = st.selectbox("性别", ["男", "女"])
            age = st.number_input("年龄", min_value=10, max_value=100, value=25)
            height = st.number_input("身高 (cm)", min_value=100, max_value=250, value=170)

        with col2:
            weight = st.number_input("体重 (kg)", min_value=30, max_value=200, value=65)
            experience = st.selectbox("健身经验", ["从未健身", "1-3个月", "3-6个月", "6-12个月", "1年以上"])
            goal = st.selectbox("健身目标", ["增肌", "减脂", "塑形", "增强体能", "康复训练"])

        available_days = st.multiselect(
            "每周可训练天数",
            ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
            default=["周一", "周三", "周五"]
        )

        available_time = st.slider(
            "每次训练时长 (分钟)",
            min_value=15,
            max_value=120,
            value=45
        )

        equipment = st.multiselect(
            "可用健身器材",
            ["徒手/自重", "哑铃", "杠铃", "健身器材", "弹力带", "壶铃"],
            default=["徒手/自重"]
        )

        injuries = st.text_area(
            "有无伤病或特殊注意 (无则留空)",
            placeholder="如：腰椎间盘突出、膝盖旧伤等"
        )

        submitted = st.form_submit_button("生成我的健身计划", use_container_width=True)

        if submitted:
            st.session_state.user_info = {
                "gender": gender,
                "age": age,
                "height": height,
                "weight": weight,
                "experience": experience,
                "goal": goal,
                "available_days": available_days,
                "available_time": available_time,
                "equipment": equipment,
                "injuries": injuries if injuries else "无"
            }

            bmi = calculate_bmi(weight, height)
            st.session_state.user_info["bmi"] = bmi

            # 生成计划
            with st.spinner("🏋️ 正在为您定制专属健身计划..."):
                plan_prompt = f"""
请根据以下用户信息，制定一份完整的健身计划：

【用户信息】
- 性别：{gender}
- 年龄：{age}岁
- 身高：{height}cm
- 体重：{weight}kg
- BMI：{bmi}
- 健身经验：{experience}
- 健身目标：{goal}
- 每周训练天数：{len(available_days)}天 ({', '.join(available_days)})
- 每次训练时长：{available_time}分钟
- 可用器材：{', '.join(equipment)}
- 特殊注意：{injuries}

请按照以下结构输出：

## 📊 身体状况分析
（根据BMI和目标分析当前身体状况）

## 🎯 训练目标与建议
（明确目标达成路径）

## 📅 每周训练计划表
（列出每周每天的具体训练内容）

## 💪 训练动作详解
（每个动作的名称、组数、次数、注意事项）

## 🥗 饮食建议
（根据目标给出饮食方案，包括热量、蛋白质摄入建议）

## ⚠️ 注意事项
（安全提醒、注意事项）

开始制定计划：
"""

                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                messages.append({"role": "user", "content": plan_prompt})

                plan = call_claude_api(messages)
                st.session_state.plan = plan
                st.session_state.plan_generated = True

                # 保存初始对话
                st.session_state.messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "assistant", "content": f"您的健身信息已录入：\n- 目标：{goal}\n- BMI：{bmi}\n\n您可以点击「我的计划」查看详细训练计划，或直接在下方咨询健身问题。"}
                ]

            st.success("✅ 计划生成完成！请点击「我的计划」查看。")

    # 显示已保存的信息
    if st.session_state.user_info:
        st.markdown("---")
        st.subheader("已保存信息")
        info = st.session_state.user_info
        cols = st.columns(4)
        cols[0].metric("性别", info["gender"])
        cols[1].metric("年龄", f"{info['age']}岁")
        cols[2].metric("身高", f"{info['height']}cm")
        cols[3].metric("体重", f"{info['weight']}kg")
        st.markdown(f"**目标：** {info['goal']}  |  **经验：** {info['experience']}  |  **BMI：** {info['bmi']}")

# ========== 页面2: 训练计划 ==========
elif st.session_state.page == "plan":
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("📋 我的健身计划")
    st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.user_info:
        st.warning("请先在「我的信息」中填写个人资料！")
    elif not st.session_state.plan_generated:
        st.warning("计划尚未生成，请先提交信息表单！")
    else:
        # 显示用户信息概览
        info = st.session_state.user_info
        with st.container():
            col1, col2, col3 = st.columns(3)
            col1.info(f"🎯 目标：{info['goal']}")
            col2.info(f"⚖️ BMI：{info['bmi']}")
            col3.info(f"📅 每周{len(info['available_days'])}练")

        st.markdown("---")
        st.markdown(st.session_state.plan)

        # 调整计划按钮
        if st.button("🔄 调整计划"):
            st.session_state.page = "chat"
            st.rerun()

# ========== 页面3: 咨询教练 ==========
elif st.session_state.page == "chat":
    # 顶部工具栏
    col1, col2, col3 = st.columns([6, 2, 2])
    with col1:
        st.markdown('<div class="main-header"><h2 style="margin:0;">💪 AI健身助手</h2></div>', unsafe_allow_html=True)
    with col2:
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col3:
        if st.button("🔄 新对话", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # 用户信息卡片
    if st.session_state.user_info:
        info = st.session_state.user_info
        with st.container():
            st.markdown("""
            <style>
                .user-info-bar {
                    background: #f8f9fa;
                    padding: 10px 20px;
                    border-radius: 8px;
                    margin: 10px 0 20px 0;
                    border-left: 4px solid #667eea;
                }
            </style>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="user-info-bar">
                <strong>👤 {info['gender']}</strong> |
                <strong>{info['age']}岁</strong> |
                <strong>{info['weight']}kg</strong> |
                <strong>BMI {info['bmi']}</strong> |
                <strong>🎯 {info['goal']}</strong>
            </div>
            """, unsafe_allow_html=True)

    # 欢迎消息
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h3>👋 欢迎来到 AI 健身助手</h3>
            <p style='color: #666;'>我是您的专业健身教练，可以帮您：</p>
            <div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; margin: 15px 0;'>
                <span style='background: #e3f2fd; padding: 8px 16px; border-radius: 20px; color: #1976d2;'>📋 制定训练计划</span>
                <span style='background: #e8f5e9; padding: 8px 16px; border-radius: 20px; color: #388e3c;'>🥗 饮食营养建议</span>
                <span style='background: #fff3e0; padding: 8px 16px; border-radius: 20px; color: #f57c00;'>💪 动作指导</span>
                <span style='background: #f3e5f5; padding: 8px 16px; border-radius: 20px; color: #7b1fa2;'>❓ 健身问答</span>
            </div>
            <p style='color: #999; margin-top: 5px;'>↓ 在下方输入框开始提问吧～ ↓</p>
        </div>
        """, unsafe_allow_html=True)

    # 显示聊天历史
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg['content'])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="💪"):
                st.markdown(msg['content'])

    # 底部输入框
    if prompt := st.chat_input("有什么健身问题想咨询？"):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 显示用户消息
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # AI回复
        with st.chat_message("assistant", avatar="💪"):
            with st.spinner("教练思考中..."):
                # 准备上下文
                context = ""
                if st.session_state.user_info:
                    info = st.session_state.user_info
                    context = f"\n\n【用户背景信息供参考】性别：{info['gender']}，年龄：{info['age']}岁，身高：{info['height']}cm，体重：{info['weight']}kg，BMI：{info['bmi']}，目标：{info['goal']}，经验：{info['experience']}\n"

                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                # 过滤掉原有的 system 消息，保留其他消息
                for msg in st.session_state.messages:
                    if msg["role"] != "system":
                        messages.append(msg)

                # 在最后一条用户消息后添加上下文
                if messages and messages[-1]["role"] == "user":
                    messages[-1]["content"] += context

                ai_reply = call_claude_api(messages)

        # 保存AI回复
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})

        # 显示AI回复
        with st.chat_message("assistant", avatar="💪"):
            st.markdown(ai_reply)

        st.rerun()

# ==================== 页脚 ====================
st.markdown("---")
st.markdown(
    """
    <div class="main-footer">
        💪 AI健身助手问答系统 | 坚持训练，遇见更好的自己<br>
        Designed by liaoxiwen
    </div>
    """,
    unsafe_allow_html=True
)
