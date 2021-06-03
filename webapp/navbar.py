from flask_login import current_user
from webapp import nav


properties = {
    "test": {
            "label": "Test",
            "class": ""
    },
    "manage_blog": {
        "label": "Manage Blog",
        "class": ""
    },
    "admin": {
        "label": "Admin",
        "class": ""
    }
}


def gen_nav():
    auto_items = []
    for feature in current_user.active_features:
        props = properties[feature]
        auto_items.append(
            nav.Item(props["label"], feature, html_attrs={'class': props["class"]})
        )
    nav.Bar(current_user.id, [
        # nav.Item('Home', 'home'),
        *auto_items,
        nav.Item('Logout', 'logout', html_attrs={'class': "right"})
    ])
