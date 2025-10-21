import streamlit as st
import requests
import urllib.parse
import base64
import json
import time
from datetime import datetime
from PIL import Image
import io
import os
import hashlib

# 页面配置
st.set_page_config(
    page_title="AI 艺术创作工作室 Pro",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
    }
    .image-card {
        border-radius: 15px;
        padding: 15px;
        background: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: all 0.3s;
        margin-bottom: 20px;
    }
    .image-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
    }
    .style-tag {
        display: inline-block;
        background: #f0f0f0;
        padding: 5px 15px;
        border-radius: 20px;
        margin: 5px;
        font-size: 0.9em;
    }
    .template-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s;
    }
    .template-card:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(245, 87, 108, 0.3);
    }
    .model-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 15px;
        font-size: 0.85em;
        font-weight: bold;
        margin: 2px;
    }
    .badge-flux { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
    .badge-sd { background: linear-gradient(135deg, #f093fb, #f5576c); color: white; }
    .badge-turbo { background: linear-gradient(135deg, #4facfe, #00f2fe); color: white; }
    .badge-premium { background: linear-gradient(135deg, #ffd89b, #19547b); color: white; }
    .scrollable-gallery {
        max-height: 800px;
        overflow-y: auto;
        padding-right: 10px;
    }
    .scrollable-gallery::-webkit-scrollbar {
        width: 8px;
    }
    .scrollable-gallery::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    .scrollable-gallery::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    .model-category {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'gallery' not in st.session_state:
    st.session_state.gallery = []
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'generation_history' not in st.session_state:
    st.session_state.generation_history = []
if 'images_to_load' not in st.session_state:
    st.session_state.images_to_load = 9
if 'total_generated' not in st.session_state:
    st.session_state.total_generated = 0

# Pollinations API配置
POLLINATIONS_API_BASE = "https://image.pollinations.ai/prompt"
POLLINATIONS_TEXT_API = "https://text.pollinations.ai"

# 完整的AI模型库（按类别分组）
AVAILABLE_MODELS = {
    "🚀 Flux 系列 - 最新高质量": {
        "Flux 1.1 Pro": {
            "model": "flux-pro-1.1", 
            "badge": "badge-flux",
            "description": "最新旗舰模型，6倍速提升，极致画质",
            "best_for": "商业作品、高要求项目"
        },
        "Flux Pro": {
            "model": "flux-pro",
            "badge": "badge-flux",
            "description": "专业级模型，顶级画质",
            "best_for": "专业摄影、艺术创作"
        },
        "Flux Realism": {
            "model": "flux-realism",
            "badge": "badge-flux",
            "description": "超写实风格，照片级效果",
            "best_for": "人像摄影、产品拍摄"
        },
        "Flux Anime": {
            "model": "flux-anime",
            "badge": "badge-flux",
            "description": "专业动漫风格",
            "best_for": "日系动漫、角色设计"
        },
        "Flux 3D": {
            "model": "flux-3d",
            "badge": "badge-flux",
            "description": "3D渲染风格",
            "best_for": "3D建模、游戏美术"
        },
        "Flux Dev": {
            "model": "flux-dev",
            "badge": "badge-flux",
            "description": "开发版本，快速迭代",
            "best_for": "概念设计、原型测试"
        },
        "Flux Schnell": {
            "model": "flux-schnell",
            "badge": "badge-turbo",
            "description": "极速生成版本",
            "best_for": "快速预览、批量生成"
        },
        "Flux (标准)": {
            "model": "flux",
            "badge": "badge-flux",
            "description": "通用标准模型",
            "best_for": "日常创作、多用途"
        }
    },
    
    "🎨 Stable Diffusion 系列": {
        "SD 3.5 Large": {
            "model": "stable-diffusion-3.5-large",
            "badge": "badge-sd",
            "description": "SD 3.5大型模型，强大性能",
            "best_for": "复杂场景、高细节"
        },
        "SD 3.5 Medium": {
            "model": "stable-diffusion-3.5-medium",
            "badge": "badge-sd",
            "description": "SD 3.5中型模型，平衡性能",
            "best_for": "平衡质量与速度"
        },
        "SD 3": {
            "model": "stable-diffusion-3",
            "badge": "badge-sd",
            "description": "Stable Diffusion 3代",
            "best_for": "文字渲染、精准构图"
        },
        "SD XL": {
            "model": "sdxl",
            "badge": "badge-sd",
            "description": "大尺寸高清模型",
            "best_for": "大幅作品、高分辨率"
        },
        "SD 2.1": {
            "model": "stable-diffusion-2.1",
            "badge": "badge-sd",
            "description": "经典稳定版本",
            "best_for": "传统风格、可靠输出"
        },
        "SD 1.5": {
            "model": "stable-diffusion-1.5",
            "badge": "badge-sd",
            "description": "经典初代模型",
            "best_for": "社区模型、微调基础"
        }
    },
    
    "⚡ 极速模型": {
        "Turbo": {
            "model": "turbo",
            "badge": "badge-turbo",
            "description": "超快速生成",
            "best_for": "实时预览、快速迭代"
        },
        "Lightning": {
            "model": "lightning",
            "badge": "badge-turbo",
            "description": "闪电级速度",
            "best_for": "批量处理、即时反馈"
        }
    },
    
    "🌟 高级专业模型": {
        "Kontext": {
            "model": "kontext",
            "badge": "badge-premium",
            "description": "BPAIGen混合模型，支持参考图",
            "best_for": "图生图、风格迁移"
        },
        "Nanobanana": {
            "model": "nanobanana",
            "badge": "badge-premium",
            "description": "Google Gemini 2.5视觉模型",
            "best_for": "自定义尺寸、参考图"
        },
        "Seedream": {
            "model": "seedream",
            "badge": "badge-premium",
            "description": "ByteDance超高清模型",
            "best_for": "高分辨率、电影级渲染"
        }
    },
    
    "🎭 特殊风格模型": {
        "Dreamshaper": {
            "model": "dreamshaper",
            "badge": "badge-sd",
            "description": "梦幻艺术风格",
            "best_for": "奇幻场景、梦境效果"
        },
        "Openjourney": {
            "model": "openjourney",
            "badge": "badge-sd",
            "description": "Midjourney开源替代",
            "best_for": "艺术创作、插画"
        },
        "Anything V5": {
            "model": "anything-v5",
            "badge": "badge-sd",
            "description": "通用动漫模型",
            "best_for": "ACG内容、二次元"
        }
    }
}

# 提示词模板库
PROMPT_TEMPLATES = {
    "人像摄影 Portrait": {
        "专业人像": "professional portrait photography, studio lighting, 85mm lens, shallow depth of field, bokeh background, sharp focus, high detail, 8K quality",
        "复古胶片": "vintage portrait, film grain, kodak portra 400, retro color grading, 1970s style, nostalgic atmosphere, analog photography",
        "时尚大片": "high fashion editorial portrait, vogue magazine style, dramatic lighting, designer clothing, runway aesthetic, professional makeup",
        "自然光": "natural light portrait, golden hour, soft diffused lighting, outdoor setting, candid moment, warm tones, lifestyle photography",
        "黑白艺术": "fine art black and white portrait, dramatic contrast, Ansel Adams style, timeless elegance, high key lighting"
    },
    "风景艺术 Landscape": {
        "中国山水": "traditional Chinese landscape painting, ink wash style, misty mountains, ancient pine trees, waterfall, tranquil atmosphere, Song dynasty aesthetic",
        "赛博朋克": "cyberpunk cityscape, neon lights reflecting on wet streets, futuristic skyscrapers, rain, night scene, blade runner aesthetic, flying cars",
        "奇幻世界": "fantasy landscape, floating islands, magical atmosphere, ethereal lighting, mystical creatures, epic vista, enchanted forest",
        "自然风光": "breathtaking natural landscape, stunning mountain vista, dramatic cloudy sky, HDR photography, wide angle, national geographic style",
        "科幻场景": "alien planet landscape, two suns in sky, strange rock formations, otherworldly plants, science fiction, concept art"
    },
    "动漫风格 Anime": {
        "日系动漫": "anime style, detailed expressive eyes, vibrant colors, cel shading, manga aesthetic, clean linework, studio lighting",
        "吉卜力风格": "Studio Ghibli animation style, soft watercolor colors, whimsical atmosphere, hand-painted look, Miyazaki inspired, dreamy clouds",
        "赛璐璐": "cel shaded anime art, bold black outlines, flat vibrant colors, Japanese animation style, 90s anime aesthetic",
        "水彩动漫": "watercolor anime illustration, soft edges, dreamy pastel atmosphere, light and airy, delicate details",
        "漫画风格": "manga illustration style, dynamic composition, speed lines, dramatic shading, black and white with screentones"
    },
    "3D 渲染 3D Render": {
        "写实渲染": "photorealistic 3D render, octane render, ray tracing, ultra detailed textures, perfect lighting, 8K quality, unreal engine",
        "皮克斯风格": "Pixar 3D animation style, cute character design, colorful, soft studio lighting, family friendly, rounded shapes",
        "低多边形": "low poly 3D art, geometric shapes, minimalist design, clean aesthetic, flat shading, isometric view",
        "科幻机械": "sci-fi 3D mechanical render, intricate details, metallic materials, panel lines, futuristic technology, hard surface modeling",
        "卡通渲染": "3D toon shader render, cartoon style, bold outlines, vibrant colors, stylized proportions, cel shaded"
    },
    "艺术流派 Art Movements": {
        "印象派": "impressionist oil painting, visible brushstrokes, emphasis on light and color, Claude Monet style, outdoor scene",
        "超现实": "surrealist art, dreamlike imagery, impossible scenes, Salvador Dali inspired, melting clocks aesthetic, subconscious imagery",
        "抽象艺术": "abstract modern art, geometric shapes, bold primary colors, Mondrian inspired, minimalist composition, contemporary",
        "波普艺术": "pop art style, bold colors, comic book aesthetic, Ben-Day dots, Andy Warhol inspired, mass culture imagery",
        "新艺术": "art nouveau style, organic flowing lines, floral motifs, Alphonse Mucha inspired, elegant curves, decorative patterns"
    },
    "概念设计 Concept Art": {
        "游戏概念": "video game concept art, detailed environment design, atmospheric perspective, fantasy RPG style, epic scale",
        "电影概念": "cinematic concept art, movie production design, dramatic lighting, epic scale, Hollywood quality, matte painting",
        "角色设计": "character concept art, multiple views, detailed costume design, turnaround sheet, professional quality, full body",
        "载具设计": "vehicle concept design, sleek futuristic design, technical details, industrial design aesthetic, blueprint style",
        "建筑概念": "architectural concept art, futuristic building design, glass and steel, modern sustainable design, aerial view"
    }
}

# 艺术风格选项
STYLE_OPTIONS = {
    "摄影风格": ["专业摄影", "电影感", "复古胶片", "HDR", "黑白", "长曝光", "微距", "航拍", "街头摄影", "纪实"],
    "绘画风格": ["油画", "水彩", "素描", "国画", "版画", "丙烯", "彩铅", "粉彩", "插画", "手绘"],
    "艺术运动": ["印象派", "立体主义", "超现实", "抽象", "波普艺术", "未来主义", "表现主义", "巴洛克", "文艺复兴", "现代主义"],
    "氛围感": ["梦幻", "神秘", "宁静", "戏剧性", "温暖", "冷峻", "浪漫", "史诗", "忧郁", "欢快"],
    "技术特效": ["光线追踪", "体积光", "景深", "运动模糊", "辉光", "粒子特效", "镜头光晕", "色差", "HDR", "全局光照"],
    "质量关键词": ["高质量", "8K", "4K", "超细节", "专业", "杰作", "获奖作品", "趋势", "史诗级", "精美"]
}

# 图片尺寸预设
IMAGE_SIZES = {
    "方形 1:1 (1024x1024)": (1024, 1024),
    "横屏 16:9 (1920x1080)": (1920, 1080),
    "竖屏 9:16 (1080x1920)": (1080, 1920),
    "横幅 21:9 (2560x1080)": (2560, 1080),
    "Instagram 4:5 (1080x1350)": (1080, 1350),
    "4K 横屏 (3840x2160)": (3840, 2160),
    "2K 方屏 (2048x2048)": (2048, 2048),
    "HD 竖屏 (1080x1920)": (1080, 1920),
    "自定义": (None, None)
}

# 辅助函数
def generate_image_url(prompt, model="flux", width=1024, height=1024, seed=None, enhance=False, nologo=True):
    """生成Pollinations API URL"""
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_API_BASE}/{encoded_prompt}"
    
    params = []
    if model and model != "flux":
        params.append(f"model={model}")
    if width:
        params.append(f"width={width}")
    if height:
        params.append(f"height={height}")
    if seed:
        params.append(f"seed={seed}")
    if enhance:
        params.append("enhance=true")
    if nologo:
        params.append("nologo=true")
    
    if params:
        url += "?" + "&".join(params)
    
    return url

def enhance_prompt_with_ai(original_prompt):
    """使用Pollinations文本API增强提示词"""
    try:
        enhancement_instruction = f"""You are an expert AI art prompt engineer. Enhance this image generation prompt by adding:
- Detailed visual descriptions
- Lighting and atmosphere details
- Art style specifications
- Quality and technical keywords

Original prompt: {original_prompt}

Enhanced prompt (respond with ONLY the enhanced prompt, no explanations):"""
        
        encoded_instruction = urllib.parse.quote(enhancement_instruction)
        url = f"{POLLINATIONS_TEXT_API}/{encoded_instruction}"
        
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            enhanced = response.text.strip()
            enhanced = enhanced.strip('"').strip("'").strip()
            return enhanced if len(enhanced) > len(original_prompt) else original_prompt
    except Exception as e:
        st.warning(f"提示词增强失败: {str(e)}")
    return original_prompt

def download_image(url):
    """下载图片"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except:
        pass
    return None

def image_to_base64(image):
    """将PIL图片转换为base64"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def generate_social_caption(prompt, styles, model):
    """生成社交媒体分享标题"""
    style_tags = " ".join([f"#{style.replace(' ', '').replace('-', '')}" for style in styles[:5]])
    caption = f"""🎨 AI艺术作品

📝 {prompt[:100]}{'...' if len(prompt) > 100 else ''}

🤖 模型: {model}
{style_tags} #AIArt #DigitalArt #AI生成 #艺术创作 #Pollinations"""
    return caption

def add_to_gallery(image_url, prompt, model, width, height, styles, seed=None):
    """添加到画廊"""
    gallery_item = {
        "id": hashlib.md5(f"{image_url}{time.time()}".encode()).hexdigest(),
        "url": image_url,
        "prompt": prompt,
        "model": model,
        "width": width,
        "height": height,
        "styles": styles,
        "seed": seed,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_favorite": False
    }
    st.session_state.gallery.insert(0, gallery_item)
    st.session_state.generation_history.insert(0, gallery_item)
    st.session_state.total_generated += 1

def toggle_favorite(item_id):
    """切换收藏状态"""
    for item in st.session_state.gallery:
        if item["id"] == item_id:
            item["is_favorite"] = not item["is_favorite"]
            if item["is_favorite"]:
                if item not in st.session_state.favorites:
                    st.session_state.favorites.append(item)
            else:
                st.session_state.favorites = [f for f in st.session_state.favorites if f["id"] != item_id]
            break

def get_model_by_name(model_name):
    """根据模型名称获取模型ID"""
    for category, models in AVAILABLE_MODELS.items():
        if model_name in models:
            return models[model_name]["model"]
    return "flux"

# 主标题
st.markdown('<h1 class="main-header">🎨 AI 艺术创作工作室 Pro</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666; font-size: 1.1em;">支持 Flux 1.1 Pro、Stable Diffusion 3.5 等 30+ 专业AI模型</p>', unsafe_allow_html=True)

# 侧边栏 - 创作控制面板
with st.sidebar:
    st.markdown("## ⚙️ 创作控制面板")
    
    # 模型选择
    st.markdown("### 🤖 选择AI模型")
    
    selected_category = st.selectbox(
        "模型类别",
        list(AVAILABLE_MODELS.keys()),
        help="选择模型类别"
    )
    
    models_in_category = AVAILABLE_MODELS[selected_category]
    
    selected_model_name = st.radio(
        "模型",
        list(models_in_category.keys()),
        help="选择具体模型",
        label_visibility="collapsed"
    )
    
    model_info = models_in_category[selected_model_name]
    st.markdown(f"""
    <div class="model-category">
        <span class="model-badge {model_info['badge']}">{selected_model_name}</span>
        <p style="margin-top: 10px; font-size: 0.9em;">{model_info['description']}</p>
        <p style="color: #667eea; font-size: 0.85em;">💡 适用于: {model_info['best_for']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    selected_model = model_info["model"]
    
    # 图片尺寸
    st.markdown("### 📐 图片尺寸")
    size_preset = st.selectbox("尺寸预设", list(IMAGE_SIZES.keys()))
    
    if size_preset == "自定义":
        col1, col2 = st.columns(2)
        with col1:
            custom_width = st.number_input("宽度", min_value=256, max_value=4096, value=1024, step=64)
        with col2:
            custom_height = st.number_input("高度", min_value=256, max_value=4096, value=1024, step=64)
        img_width, img_height = custom_width, custom_height
    else:
        img_width, img_height = IMAGE_SIZES[size_preset]
    
    st.info(f"📏 当前尺寸: {img_width} x {img_height} px")
    
    # 高级设置
    st.markdown("### 🎛️ 高级设置")
    
    use_seed = st.checkbox("使用固定种子")
    seed_value = None
    if use_seed:
        seed_value = st.number_input("种子值", min_value=0, max_value=999999999, value=42, step=1)
        st.caption("💡 相同种子+提示词=相同图片")
    
    use_ai_enhance = st.checkbox("AI提示词增强 ✨", value=False)
    
    batch_mode = st.checkbox("批量生成模式 🔄")
    batch_count = 1
    if batch_mode:
        batch_count = st.slider("生成数量", min_value=1, max_value=10, value=4)
        st.caption(f"将生成 {batch_count} 张变体")
    
    # 统计信息
    st.markdown("---")
    st.markdown("### 📊 创作统计")
    st.markdown(f"""
    <div class="stats-card">
        <h3>{st.session_state.total_generated}</h3>
        <p>总生成数</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="stats-card">
        <h3>{len(st.session_state.favorites)}</h3>
        <p>收藏作品</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="stats-card">
        <h3>{len(st.session_state.gallery)}</h3>
        <p>画廊作品</p>
    </div>
    """, unsafe_allow_html=True)

# 主内容区 - 标签页
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎨 创作工作台", 
    "📚 提示词模板库", 
    "🤖 模型对比", 
    "🖼️ 作品画廊", 
    "⭐ 我的收藏", 
    "📜 生成历史"
])

# Tab 1: 创作工作台
with tab1:
    st.markdown("## 🎨 开始创作你的AI艺术作品")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        user_prompt = st.text_area(
            "📝 描述你想要的艺术作品",
            height=150,
            placeholder="例如：一个赛博朋克风格的女战士，霓虹灯背景，未来主义城市，高细节，8K画质...",
            help="详细描述你想要生成的图像"
        )
    
    with col2:
        st.markdown("### ")
        if st.button("🚀 立即生成", type="primary", use_container_width=True):
            if user_prompt:
                with st.spinner(f"🎨 正在使用 {selected_model_name} 生成{batch_count}张作品..."):
                    final_prompt = user_prompt
                    if use_ai_enhance:
                        with st.spinner("✨ AI正在增强提示词..."):
                            final_prompt = enhance_prompt_with_ai(user_prompt)
                            if final_prompt != user_prompt:
                                st.success(f"✨ 提示词已增强！")
                                with st.expander("查看增强后的提示词"):
                                    st.code(final_prompt, language=None)
                    
                    progress_bar = st.progress(0)
                    for i in range(batch_count):
                        current_seed = seed_value + i if seed_value else None
                        image_url = generate_image_url(
                            final_prompt,
                            model=selected_model,
                            width=img_width,
                            height=img_height,
                            seed=current_seed,
                            enhance=False,
                            nologo=True
                        )
                        
                        add_to_gallery(
                            image_url,
                            final_prompt,
                            selected_model_name,
                            img_width,
                            img_height,
                            [],
                            current_seed
                        )
                        progress_bar.progress((i + 1) / batch_count)
                    
                    st.success(f"✅ 成功生成 {batch_count} 张作品！")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("⚠️ 请输入提示词")
        
        st.markdown("---")
        if st.button("🎲 随机灵感", use_container_width=True):
            random_templates = []
            for category in PROMPT_TEMPLATES.values():
                random_templates.extend(list(category.values()))
            import random
            random_prompt = random.choice(random_templates)
            st.info(f"💡 {random_prompt}")
    
    # 风格混合区
    st.markdown("---")
    st.markdown("### 🎭 风格混合器")
    
    selected_styles = []
    style_cols = st.columns(len(STYLE_OPTIONS))
    
    for idx, (category, styles) in enumerate(STYLE_OPTIONS.items()):
        with style_cols[idx]:
            with st.expander(f"📂 {category}", expanded=False):
                for style in styles:
                    if st.checkbox(style, key=f"style_{category}_{style}"):
                        selected_styles.append(style)
    
    if selected_styles:
        st.markdown("**✨ 已选风格：**")
        style_html = "".join([f'<span class="style-tag">{style}</span>' for style in selected_styles])
        st.markdown(style_html, unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("➕ 添加到提示词"):
                style_text = ", ".join(selected_styles)
                combined = f"{user_prompt}, {style_text}" if user_prompt else style_text
                st.code(combined, language=None)
        
        with col_b:
            if st.button("🚀 使用风格生成"):
                if user_prompt:
                    style_text = ", ".join(selected_styles)
                    combined = f"{user_prompt}, {style_text}"
                    
                    with st.spinner("生成中..."):
                        image_url = generate_image_url(
                            combined,
                            model=selected_model,
                            width=img_width,
                            height=img_height,
                            seed=seed_value,
                            nologo=True
                        )
                        add_to_gallery(image_url, combined, selected_model_name, img_width, img_height, selected_styles, seed_value)
                        st.success("✅ 生成完成！")
                        st.rerun()
                else:
                    st.warning("请先输入提示词")
    
    # 最新作品预览
    if st.session_state.gallery:
        st.markdown("---")
        st.markdown("### 🖼️ 最新作品")
        cols = st.columns(min(4, len(st.session_state.gallery[:4])))
        for idx, item in enumerate(st.session_state.gallery[:4]):
            with cols[idx]:
                st.image(item["url"], use_container_width=True)
                st.caption(f"🤖 {item['model']}")

# Tab 2: 提示词模板库
with tab2:
    st.markdown("## 📚 专业提示词模板库")
    
    search_term = st.text_input("🔍 搜索模板", placeholder="输入关键词...")
    
    for category, templates in PROMPT_TEMPLATES.items():
        if search_term:
            filtered = {k: v for k, v in templates.items() if search_term.lower() in k.lower() or search_term.lower() in v.lower()}
            if not filtered:
                continue
            templates = filtered
        
        st.markdown(f"### {category}")
        cols = st.columns(2)
        
        for idx, (name, template) in enumerate(templates.items()):
            with cols[idx % 2]:
                st.markdown(f"""
                <div class="template-card">
                    <h4>✨ {name}</h4>
                    <p style="font-size:0.9em; opacity:0.95; margin-top: 10px;">{template[:100]}...</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns([1, 1, 1])
                
                with col_a:
                    if st.button("📋", key=f"copy_{category}_{name}"):
                        with st.expander("完整提示词", expanded=True):
                            st.code(template, language=None)
                
                with col_b:
                    if st.button("🚀", key=f"gen_{category}_{name}"):
                        with st.spinner("生成中..."):
                            image_url = generate_image_url(
                                template,
                                model=selected_model,
                                width=img_width,
                                height=img_height,
                                seed=seed_value,
                                nologo=True
                            )
                            add_to_gallery(image_url, template, selected_model_name, img_width, img_height, [name], seed_value)
                            st.success("✅ 完成！")
                            time.sleep(0.5)
                            st.rerun()
                
                with col_c:
                    if st.button("✨", key=f"enhance_{category}_{name}"):
                        with st.spinner("增强中..."):
                            enhanced = enhance_prompt_with_ai(template)
                            image_url = generate_image_url(
                                enhanced,
                                model=selected_model,
                                width=img_width,
                                height=img_height,
                                nologo=True
                            )
                            add_to_gallery(image_url, enhanced, selected_model_name, img_width, img_height, [name])
                            st.success("✅ 完成！")
                            st.rerun()

# Tab 3: 模型对比
with tab3:
    st.markdown("## 🤖 AI模型完整对比")
    
    for category, models in AVAILABLE_MODELS.items():
        st.markdown(f"### {category}")
        
        for model_name, model_info in models.items():
            with st.expander(f"🔹 {model_name}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    **模型ID:** `{model_info['model']}`
                    
                    **描述:** {model_info['description']}
                    
                    **最适合:** {model_info['best_for']}
                    """)
                
                with col2:
                    st.markdown(f'<span class="model-badge {model_info["badge"]}">{model_name}</span>', unsafe_allow_html=True)
        
        st.markdown("---")
    
    st.markdown("### 💡 使用建议")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🚀 追求速度**
        - Turbo
        - Lightning
        - Flux Schnell
        """)
    
    with col2:
        st.markdown("""
        **🎨 追求质量**
        - Flux 1.1 Pro
        - Flux Pro
        - SD 3.5 Large
        """)
    
    with col3:
        st.markdown("""
        **💰 平衡选择**
        - Flux (标准)
        - SD 3
        - Flux Dev
        """)

# Tab 4: 作品画廊
with tab4:
    st.markdown("## 🖼️ 作品画廊")
    
    if st.session_state.gallery:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            filter_model = st.multiselect(
                "按模型筛选",
                options=list(set([item["model"] for item in st.session_state.gallery])),
                default=[]
            )
        
        with col2:
            sort_by = st.selectbox("排序", ["最新", "最旧", "仅收藏"])
        
        with col3:
            view_mode = st.selectbox("视图", ["网格", "列表"])
        
        with col4:
            if st.button("🗑️"):
                st.session_state.gallery = []
                st.rerun()
        
        filtered_gallery = st.session_state.gallery
        if filter_model:
            filtered_gallery = [item for item in filtered_gallery if item["model"] in filter_model]
        
        if sort_by == "最旧":
            filtered_gallery = list(reversed(filtered_gallery))
        elif sort_by == "仅收藏":
            filtered_gallery = [item for item in filtered_gallery if item["is_favorite"]]
        
        total_images = len(filtered_gallery)
        st.markdown(f"**共 {total_images} 张作品**")
        
        if filtered_gallery:
            images_to_show = filtered_gallery[:st.session_state.images_to_load]
            
            if view_mode == "网格":
                for i in range(0, len(images_to_show), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(images_to_show):
                            item = images_to_show[i + j]
                            with cols[j]:
                                st.markdown('<div class="image-card">', unsafe_allow_html=True)
                                st.image(item["url"], use_container_width=True)
                                
                                st.markdown(f"**{item['prompt'][:50]}...**")
                                st.caption(f"🤖 {item['model']} | 📐 {item['width']}x{item['height']}")
                                st.caption(f"🕐 {item['timestamp']}")
                                
                                col_a, col_b, col_c, col_d = st.columns(4)
                                
                                with col_a:
                                    fav_icon = "⭐" if item["is_favorite"] else "☆"
                                    if st.button(fav_icon, key=f"fav_{item['id']}"):
                                        toggle_favorite(item['id'])
                                        st.rerun()
                                
                                with col_b:
                                    if st.button("📥", key=f"dl_{item['id']}"):
                                        img = download_image(item["url"])
                                        if img:
                                            buf = io.BytesIO()
                                            img.save(buf, format="PNG")
                                            st.download_button(
                                                "💾",
                                                buf.getvalue(),
                                                file_name=f"ai_art_{item['id'][:8]}.png",
                                                mime="image/png",
                                                key=f"dlbtn_{item['id']}"
                                            )
                                
                                with col_c:
                                    if st.button("🔄", key=f"regen_{item['id']}"):
                                        with st.spinner("重新生成..."):
                                            model_id = get_model_by_name(item["model"])
                                            new_url = generate_image_url(
                                                item["prompt"],
                                                model=model_id,
                                                width=item["width"],
                                                height=item["height"],
                                                nologo=True
                                            )
                                            add_to_gallery(new_url, item["prompt"], item["model"], item["width"], item["height"], item["styles"])
                                            st.rerun()
                                
                                with col_d:
                                    if st.button("📤", key=f"share_{item['id']}"):
                                        caption = generate_social_caption(item["prompt"], item["styles"], item["model"])
                                        st.text_area("分享", caption, height=150, key=f"cap_{item['id']}")
                                
                                st.markdown('</div>', unsafe_allow_html=True)
            
            if len(images_to_show) < total_images:
                if st.button(f"📜 加载更多 (还有 {total_images - len(images_to_show)} 张)"):
                    st.session_state.images_to_load += 9
                    st.rerun()
        else:
            st.info("没有符合条件的作品")
    else:
        st.info("🎨 画廊是空的，开始创作吧！")

# Tab 5: 我的收藏
with tab5:
    st.markdown("## ⭐ 我的收藏")
    
    if st.session_state.favorites:
        st.markdown(f"共 **{len(st.session_state.favorites)}** 件收藏")
        
        for i in range(0, len(st.session_state.favorites), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(st.session_state.favorites):
                    item = st.session_state.favorites[i + j]
                    with cols[j]:
                        st.image(item["url"], use_container_width=True)
                        st.markdown(f"**{item['prompt'][:50]}...**")
                        st.caption(f"🤖 {item['model']}")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("💔", key=f"unfav_{item['id']}"):
                                toggle_favorite(item['id'])
                                st.rerun()
                        
                        with col_b:
                            img = download_image(item["url"])
                            if img:
                                buf = io.BytesIO()
                                img.save(buf, format="PNG")
                                st.download_button(
                                    "📥",
                                    buf.getvalue(),
                                    file_name=f"fav_{item['id'][:8]}.png",
                                    mime="image/png",
                                    key=f"dlfav_{item['id']}"
                                )
    else:
        st.info("⭐ 还没有收藏，去画廊收藏作品吧！")

# Tab 6: 生成历史
with tab6:
    st.markdown("## 📜 生成历史")
    
    if st.session_state.generation_history:
        st.markdown(f"共 **{len(st.session_state.generation_history)}** 张")
        
        col1, col2 = st.columns(2)
        
        with col1:
            history_json = json.dumps(st.session_state.generation_history, ensure_ascii=False, indent=2)
            st.download_button(
                "📥 导出JSON",
                history_json,
                file_name=f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            if st.button("🗑️ 清空历史"):
                st.session_state.generation_history = []
                st.rerun()
        
        st.markdown("---")
        
        show_limit = st.slider("显示数量", 10, 100, 20, 10)
        
        for idx, item in enumerate(st.session_state.generation_history[:show_limit]):
            with st.expander(f"#{idx+1} | {item['timestamp']} | {item['model']}"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(item["url"], use_container_width=True)
                
                with col2:
                    st.markdown("**提示词:**")
                    st.code(item['prompt'], language=None)
                    st.markdown(f"**模型:** {item['model']}")
                    st.markdown(f"**尺寸:** {item['width']} x {item['height']}")
                    if item.get("seed"):
                        st.markdown(f"**种子:** {item['seed']}")
                    
                    if st.button("🔄 复用配置", key=f"reuse_{item['id']}"):
                        with st.spinner("生成中..."):
                            model_id = get_model_by_name(item["model"])
                            new_url = generate_image_url(
                                item["prompt"],
                                model=model_id,
                                width=item["width"],
                                height=item["height"],
                                seed=item.get("seed"),
                                nologo=True
                            )
                            add_to_gallery(new_url, item["prompt"], item["model"], item["width"], item["height"], item["styles"], item.get("seed"))
                            st.success("完成！")
                            st.rerun()
    else:
        st.info("📜 还没有历史记录")

# 页脚
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 30px;">
    <h3 style="color: #667eea;">🎨 AI 艺术创作工作室 Pro</h3>
    <p style="font-size: 1.1em; margin: 15px 0;">Powered by Pollinations.AI</p>
    <p style="font-size: 0.95em;">支持 30+ 专业AI模型 | Flux 1.1 Pro · SD 3.5 · Turbo</p>
    <p style="font-size: 0.9em; margin-top: 15px;">✨ 释放创造力，让AI成为你的艺术伙伴 ✨</p>
</div>
""", unsafe_allow_html=True)
