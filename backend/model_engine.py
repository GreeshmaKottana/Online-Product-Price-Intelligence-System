import torch
import clip
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading CLIP model...")
model, preprocess = clip.load("ViT-B/32", device=device)
print("CLIP model loaded successfully")


# Product categories with better prompts for CLIP
PRODUCT_CATEGORIES = [

# Electronics
"a photo of a smartphone",
"a photo of a laptop computer",
"a photo of a tablet device",
"a photo of a desktop computer",
"a photo of a computer monitor",
"a photo of a keyboard",
"a photo of a computer mouse",
"a photo of a gaming mouse",
"a photo of a gaming keyboard",
"a photo of a printer",
"a photo of a scanner",
"a photo of a wifi router",
"a photo of a modem",
"a photo of an external hard drive",
"a photo of an ssd storage device",
"a photo of a usb flash drive",
"a photo of a graphics card gpu",
"a photo of a computer motherboard",
"a photo of a cpu processor",
"a photo of a webcam",
"a photo of a microphone",
"a photo of speakers",
"a photo of headphones",
"a photo of wireless earbuds",
"a photo of a smartwatch",
"a photo of a fitness tracker band",
"a photo of a digital camera",
"a photo of a dslr camera",
"a photo of a camera tripod",
"a photo of a drone quadcopter",

# Clothing
"a photo of a t-shirt",
"a photo of a casual shirt",
"a photo of a polo shirt",
"a photo of a hoodie",
"a photo of a jacket",
"a photo of a coat",
"a photo of a sweater",
"a photo of jeans pants",
"a photo of trousers",
"a photo of shorts",
"a photo of a dress",
"a photo of a skirt",
"a photo of a suit",
"a photo of a blazer",
"a photo of a sweatshirt",
"a photo of a tracksuit",
"a photo of socks",
"a photo of underwear",
"a photo of a sports bra",
"a photo of a swimsuit",
"a photo of a raincoat",

# Footwear
"a photo of shoes",
"a photo of sneakers",
"a photo of running shoes",
"a photo of sandals",
"a photo of boots",
"a photo of high heels",
"a photo of flip flops",
"a photo of loafers",

# Bags
"a photo of a backpack",
"a photo of a handbag",
"a photo of a laptop bag",
"a photo of a travel bag",
"a photo of a duffel bag",
"a photo of a wallet",
"a photo of a purse",
"a photo of a school bag",

# Appliances
"a photo of a refrigerator",
"a photo of a washing machine",
"a photo of a microwave oven",
"a photo of an oven",
"a photo of a coffee maker",
"a photo of a blender",
"a photo of a toaster",
"a photo of a dishwasher",
"a photo of an air conditioner",
"a photo of a room heater",
"a photo of a fan",
"a photo of a vacuum cleaner",

# Furniture
"a photo of a chair",
"a photo of an office chair",
"a photo of a table",
"a photo of a desk",
"a photo of a sofa",
"a photo of a bed",
"a photo of a bookshelf",
"a photo of a wardrobe",
"a photo of a cabinet",
"a photo of a nightstand",

# Kitchen
"a photo of a kitchen knife",
"a photo of a cutting board",
"a photo of a frying pan",
"a photo of a pressure cooker",
"a photo of a water bottle",
"a photo of a lunch box",
"a photo of a mug",
"a photo of a plate",
"a photo of a bowl",

# Beauty
"a photo of lipstick",
"a photo of perfume",
"a photo of foundation makeup",
"a photo of moisturizer",
"a photo of face cream",
"a photo of shampoo",
"a photo of conditioner",
"a photo of a hair dryer",

# Toys
"a photo of lego blocks",
"a photo of an action figure toy",
"a photo of a toy car",
"a photo of a board game",
"a photo of a puzzle toy",
"a photo of a doll",
"a photo of a video game console",

# Sports
"a photo of a football",
"a photo of a basketball",
"a photo of a tennis racket",
"a photo of a cricket bat",
"a photo of a yoga mat",
"a photo of dumbbells",
"a photo of a treadmill",

# Misc
"a photo of a book",
"a photo of a notebook",
"a photo of a pen",
"a photo of a calculator",
"a photo of a wrist watch",
"a photo of a wall clock",
"a photo of a lamp",
"a photo of a desk lamp",
"a photo of a power bank"
]


def identify_product(image_path):
    try:

        image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
        text = clip.tokenize(PRODUCT_CATEGORIES).to(device)

        with torch.no_grad():
            image_features = model.encode_image(image)
            text_features = model.encode_text(text)

            logits = (image_features @ text_features.T).softmax(dim=-1)

        probs = logits.cpu().numpy()[0]

        # Top predictions instead of just one
        top_indices = probs.argsort()[-5:][::-1]

        best_index = top_indices[0]

        keywords = [
            PRODUCT_CATEGORIES[i].replace("a photo of a ", "").replace("a photo of ", "")
            for i in top_indices
        ]

        return {
            "status": "success",
            "analysis": {
                "category": keywords[0],
                "confidence": round(float(probs[best_index] * 100), 2)
            },
            "keywords": keywords
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }