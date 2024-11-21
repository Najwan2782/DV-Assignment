import flet, flet_core.types

def main(page: flet.Page) -> None:
    page.title = f"My Coffee Shop Menu"
    my_coffee_shop_text: flet.Text = flet.Text(f"My Coffee Shop Menu", size=100)

    espresso_text: flet.Text = flet.Text(f"Espresso", size=20)
    espresso_image: flet.Image = flet.Image(src=f"images/ecspresso.jpeg", width=100, height=100)
    espresso_price: flet.Text = flet.Text(f"RM 4.90", size=20)

    americano_text: flet.Text = flet.Text(f"Americano", size=20)
    americano_image: flet.Image = flet.Image(src=f"images/americano.jpeg", width=100, height=100)
    americano_price: flet.Text = flet.Text(f"RM 6.90", size=20)

    capucino_text: flet.Text = flet.Text(f"Capucino", size=20)
    capucino_image: flet.Image = flet.Image(src=f"images/capucino.jpeg", width=100, height=100)
    capucino_price: flet.Text = flet.Text(f"RM 9.90", size=20)

    latte_text: flet.Text = flet.Text(f"Latte", size=20)
    latte_image: flet.Image = flet.Image(src=f"images/latte.jpeg", width=100, height=100)
    latte_price: flet.Text = flet.Text(f"RM 9.90", size=20)

    mocha_text: flet.Text = flet.Text(f"Mocha", size=20)
    mocha_image: flet.Image = flet.Image(src=f"images/mocha.jpeg", width=100, height=100)
    mocha_price: flet.Text = flet.Text(f"RM 11.90", size=20)

    ice_espresso_text: flet.Text = flet.Text(f"Ice Espresso", size=20)
    ice_espresso_image: flet.Image = flet.Image(src=f"images/ice_espresso.jpeg", width=100, height=100)
    ice_espresso_price: flet.Text = flet.Text(f"RM 6.90", size=20)

    ice_americano_text: flet.Text = flet.Text(f"Ice Americano", size=20)
    ice_americano_image: flet.Image = flet.Image(src=f"images/ice_americano.jpeg", width=100, height=100)
    ice_americano_price: flet.Text = flet.Text(f"RM 8.90", size=20)

    ice_capucino_text: flet.Text = flet.Text(f"Ice Cappucino", size=20)
    ice_capucino_image: flet.Image = flet.Image(src=f"images/ice_capucino.jpeg", width=100, height=100)
    ice_capucino_price: flet.Text = flet.Text(f"RM 11.90", size=20)

    ice_latte_text: flet.Text = flet.Text(f"Ice Latte", size=20)
    ice_latte_image: flet.Image = flet.Image(src=f"images/ice_latte.jpeg", width=100, height=100)
    ice_latte_price: flet.Text = flet.Text(f"RM 11.90", size=20)

    ice_mocha_text: flet.Text = flet.Text(f"Ice Mocha", size=20)
    ice_mocha_image: flet.Image = flet.Image(src=f"images/ice_mocha.jpeg", width=100, height=100)
    ice_mocha_price: flet.Text = flet.Text(f"RM 13.90", size=20)
    
    page.add(flet.Row([my_coffee_shop_text]), flet.Row([flet.Column([espresso_text, espresso_image, espresso_price]), flet.Column([americano_text, americano_image, americano_price]), flet.Column([capucino_text, capucino_image, capucino_price]), flet.Column([latte_text, latte_image, latte_price]), flet.Column([mocha_text, mocha_image, mocha_price]), flet.Column([ice_espresso_text, ice_espresso_image, ice_espresso_price]), flet.Column([ice_americano_text, ice_americano_image, ice_americano_price]), flet.Column([ice_capucino_text, ice_capucino_image, ice_capucino_price]), flet.Column([ice_latte_text, ice_latte_image, ice_latte_price]), flet.Column([ice_mocha_text, ice_mocha_image, ice_mocha_price])]))

    page.update()

if __name__ == f"__main__":
    flet.app(target=main, view=flet_core.types.WEB_BROWSER, assets_dir=f"assets")