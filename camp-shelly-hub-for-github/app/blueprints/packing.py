from flask import Blueprint, render_template

bp = Blueprint("packing", __name__, url_prefix="/packing-list")


PACKING_LIST = [
    ("Sleeping", [
        "Tent (check stakes, poles, rainfly)",
        "Sleeping bag rated for nighttime lows",
        "Sleeping pad or air mattress + pump",
        "Pillow",
        "Extra blanket",
    ]),
    ("Clothing", [
        "Layers (mornings and nights get cold)",
        "Rain jacket",
        "Hat / sun hat",
        "Closed-toe shoes for the trail",
        "Sandals or camp shoes",
        "Swimsuit",
        "Warm socks",
    ]),
    ("Toiletries", [
        "Toothbrush + toothpaste",
        "Soap / shampoo (biodegradable if rinsing outdoors)",
        "Towel + shower shoes",
        "Sunscreen",
        "Bug spray",
        "Any prescription meds",
    ]),
    ("Food", [
        "Meals for your household (see Meal Ideas)",
        "Snacks",
        "Water bottle",
        "Coffee + filter / kettle if you must",
    ]),
    ("Cooking", [
        "Camp stove + fuel",
        "Lighter / matches",
        "Cookware + utensils",
        "Plates, bowls, cups",
        "Dish soap, sponge, dish towel",
        "Cooler + ice",
        "Trash bags",
    ]),
    ("Lighting", [
        "Headlamp + batteries",
        "Lantern",
        "Backup flashlight",
    ]),
    ("Kids / Youth", [
        "Comfort item / stuffed animal",
        "Activity / craft supplies",
        "Glow sticks (campfire favorite)",
        "Extra clothes (kids change clothes 6 times a day, apparently)",
    ]),
    ("Comfort items", [
        "Camp chair",
        "Hammock",
        "Book / journal",
        "Earplugs",
    ]),
    ("Safety", [
        "First aid kit",
        "Whistle",
        "Pocket knife / multi-tool",
        "Emergency contact info card",
    ]),
    ("Optional extras", [
        "Camera",
        "Musical instrument",
        "Games",
        "Star chart / binoculars",
    ]),
]

FIRST_TIMER_BASICS = [
    "Tent + sleeping bag + sleeping pad — the big 3",
    "Headlamp (you'll use it more than you expect)",
    "Camp chair",
    "Water bottle",
    "Closed-toe shoes",
    "Layers + rain jacket",
    "Towel + shower shoes",
    "Toothbrush + toiletries",
    "Bug spray + sunscreen",
    "Snacks",
]


@bp.route("/")
def index():
    return render_template("packing/index.html",
                           packing_list=PACKING_LIST,
                           first_timer=FIRST_TIMER_BASICS)
