import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import streamlit as st

st.set_page_config(
    page_title="FitCheck — Virtual Try-On",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&family=Cormorant+Garamond:wght@600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0e0e0e !important;
    color: #e8e8e8 !important;
}
.main, .block-container {
    background-color: #0e0e0e !important;
    padding: 2.5rem 3rem;
    max-width: 1100px;
}
.hero-title {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 4.5rem !important;
    font-weight: 600 !important;
    color: #f5f5f5 !important;
    line-height: 1.1 !important;
    margin-bottom: 0.75rem !important;
    display: block;
}
.hero-sub {
    font-size: 1rem;
    color: #666;
    font-weight: 300;
    margin-bottom: 1.5rem;
}
.step-label {
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #555;
    margin-bottom: 0.3rem;
}
.step-title {
    font-size: 1rem;
    font-weight: 500;
    color: #ccc;
    margin-bottom: 0.8rem;
}
.badge {
    display: inline-block;
    background: #1a2e1a;
    color: #5cc87a;
    font-size: 0.72rem;
    font-weight: 500;
    padding: 3px 12px;
    border-radius: 20px;
    margin-bottom: 0.8rem;
}
.divider {
    border: none;
    border-top: 1px solid #222;
    margin: 1.5rem 0;
}
section[data-testid="stSidebar"] {
    background-color: #111 !important;
    border-right: 1px solid #1e1e1e !important;
}
section[data-testid="stSidebar"] * { color: #aaa !important; }
section[data-testid="stSidebar"] input {
    background: #1a1a1a !important;
    border: 1px solid #333 !important;
    color: #fff !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
    color: #e8e8e8 !important;
    padding: 0.6rem 1rem !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: #444 !important;
    box-shadow: none !important;
}
.stFileUploader > div {
    background: #1a1a1a !important;
    border: 1px dashed #2a2a2a !important;
    border-radius: 10px !important;
}
.stButton > button {
    background: #f5f5f5 !important;
    color: #0e0e0e !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    width: 100% !important;
}
.stButton > button:hover { background: #ddd !important; }
.stDownloadButton > button {
    background: transparent !important;
    color: #888 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
    width: 100% !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stDownloadButton > button:hover {
    border-color: #444 !important;
    color: #ccc !important;
}
img { border-radius: 12px !important; }
.stSpinner > div { border-top-color: #f5f5f5 !important; }
.stCaption { color: #555 !important; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─── Scraper ───────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive",
}

def scrape_product_image(url, save_path="output/garment.jpg"):
    os.makedirs("output", exist_ok=True)

    # Direct image URL — download straight away
    if any(url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
        return download_image(url, save_path)

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        st.error(f"Could not reach that URL: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return download_image(og["content"], save_path)

    twitter = soup.find("meta", attrs={"name": "twitter:image"})
    if twitter and twitter.get("content"):
        return download_image(twitter["content"], save_path)

    for img_tag in soup.find_all("img"):
        src = img_tag.get("src", "")
        if src.startswith("http") and any(x in src for x in ["product", "item", "medium", "large", "zoom"]):
            return download_image(src, save_path)

    st.error("Could not find a product image. Use the 'Upload image' option instead.")
    return None


def download_image(url, save_path):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        img.save(save_path)
        return img
    except Exception as e:
        st.error(f"Failed to download image: {e}")
        return None


# ─── Try-On ────────────────────────────────────────────────────────────────────

def run_tryon(garment_path, user_path, hf_token):
    try:
        from gradio_client import Client, handle_file
        import httpx
        client = Client(
            "yisol/IDM-VTON",
            token=hf_token,
            httpx_kwargs={"timeout": httpx.Timeout(300.0)}
        )
        result = client.predict(
            dict={
                "background": handle_file(user_path),
                "layers": [handle_file(user_path)],
                "composite": None
            },
            garm_img=handle_file(garment_path),
            garment_des="upper body fashion garment",
            is_checked=True,
            is_checked_crop=True,
            denoise_steps=40,
            seed=42,
            api_name="/tryon"
        )
        return Image.open(result[0])
    except Exception as e:
        st.error(f"Try-on failed: {e}")
        return None


# ─── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ✦ FitCheck")
    st.markdown("<p style='font-size:0.8rem;color:#555;margin-bottom:1.5rem'>AI Virtual Try-On</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.8rem;color:#777;margin-bottom:0.3rem'>Hugging Face Token</p>", unsafe_allow_html=True)
    hf_token = st.text_input("hf_token", type="password", placeholder="hf_...", label_visibility="collapsed")
    st.markdown("<p style='font-size:0.72rem;color:#444;margin-top:0.4rem'>huggingface.co → Settings → Tokens</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<p style='font-size:0.78rem;color:#555'>Tips for best results</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.75rem;color:#444;line-height:1.8'>· Full body photo, facing forward<br>· Plain or simple background<br>· Good lighting<br>· Solid colour garments work best</p>", unsafe_allow_html=True)


# ─── Hero ──────────────────────────────────────────────────────────────────────

st.markdown('<span class="hero-title">Try it before<br>you buy it.</span>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Paste any fashion product link, upload your photo — see how it looks on you.</p>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── Steps ─────────────────────────────────────────────────────────────────────

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<p class="step-label">Step 01</p>', unsafe_allow_html=True)
    st.markdown('<p class="step-title">Add a garment</p>', unsafe_allow_html=True)

    input_method = st.radio("", ["Paste product URL", "Upload image"], horizontal=True, label_visibility="collapsed")

    garment_img = None

    if input_method == "Paste product URL":
        product_url = st.text_input("product_url", placeholder="https://www.zara.com/...", label_visibility="collapsed")
        st.caption("Works on Zara, H&M, ASOS, Myntra. For other sites use 'Upload image'.")
        if product_url:
            with st.spinner("Fetching garment..."):
                garment_img = scrape_product_image(product_url)
            if garment_img:
                st.markdown('<span class="badge">✓ Garment found</span>', unsafe_allow_html=True)
                st.image(garment_img, use_container_width=True)
    else:
        garment_upload = st.file_uploader("Upload garment image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        st.caption("Save the product image from any website and upload it here.")
        if garment_upload:
            garment_img = Image.open(garment_upload).convert("RGB")
            os.makedirs("output", exist_ok=True)
            garment_img.save("output/garment.jpg")
            st.markdown('<span class="badge">✓ Garment ready</span>', unsafe_allow_html=True)
            st.image(garment_img, use_container_width=True)

with col2:
    st.markdown('<p class="step-label">Step 02</p>', unsafe_allow_html=True)
    st.markdown('<p class="step-title">Upload your photo</p>', unsafe_allow_html=True)
    user_photo = st.file_uploader("user_photo", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

    user_img = None
    if user_photo:
        user_img = Image.open(user_photo).convert("RGB")
        os.makedirs("output", exist_ok=True)
        user_img.save("output/user.jpg")
        st.markdown('<span class="badge">✓ Photo ready</span>', unsafe_allow_html=True)
        st.image(user_img, use_container_width=True)

# ─── Generate ──────────────────────────────────────────────────────────────────

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<p class="step-label">Step 03</p>', unsafe_allow_html=True)
st.markdown('<p class="step-title">Generate your look</p>', unsafe_allow_html=True)

if garment_img and user_img and hf_token:
    if st.button("✦ Try it on"):
        with st.spinner("Generating your look — takes 30–60 seconds..."):
            result = run_tryon("output/garment.jpg", "output/user.jpg", hf_token)
        if result:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('<p class="step-label">Your look</p>', unsafe_allow_html=True)
            r1, r2, r3 = st.columns(3, gap="medium")
            r1.image(garment_img, caption="Garment", use_container_width=True)
            r2.image(user_img, caption="You", use_container_width=True)
            r3.image(result, caption="Result ✦", use_container_width=True)
            result.save("output/result.jpg")
            with open("output/result.jpg", "rb") as f:
                st.download_button("↓ Download your look", f, "fitcheck_result.jpg", "image/jpeg")
elif not hf_token:
    st.caption("Add your Hugging Face token in the sidebar to get started.")
elif not garment_img:
    st.caption("Add a garment above to continue.")
elif not user_img:
    st.caption("Upload your photo above to continue.")
