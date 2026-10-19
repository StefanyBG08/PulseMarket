
from playwright.sync_api import expect


def test_dashboard_productos_y_pedidos(page):
    # Abrir el dashboard.
    page.goto("http://127.0.0.1:5000")

    expect(
        page.get_by_role("heading", name="Dashboard")
    ).to_be_visible()

    # Registrar un producto desde la interfaz.
    nombre_producto = "Producto E2E"

    page.locator(
        "#productForm input[name='nombre']"
    ).fill(nombre_producto)

    page.locator(
        "#productForm input[name='categoria']"
    ).fill("Pruebas")

    page.locator(
        "#productForm input[name='precio']"
    ).fill("125")

    page.locator(
        "#productForm input[name='stock']"
    ).fill("8")

    page.locator(
        "#productForm button[type='submit']"
    ).click()

    expect(page.locator("#formMessage")).to_have_text(
        "Producto agregado correctamente."
    )

    expect(
        page.locator("#productsTable")
    ).to_contain_text(nombre_producto)

    # Registrar un pedido desde la interfaz.
    nombre_cliente = "Cliente E2E"

    page.locator(
        "#orderForm input[name='cliente']"
    ).fill(nombre_cliente)

    page.locator(
        "#orderForm input[name='producto']"
    ).fill(nombre_producto)

    page.locator(
        "#orderForm input[name='total']"
    ).fill("125")

    page.locator(
        "#orderForm select[name='estado']"
    ).select_option("Completado")

    page.locator(
        "#orderForm button[type='submit']"
    ).click()

    expect(page.locator("#formMessage")).to_have_text(
        "Pedido registrado correctamente."
    )

    # Comprobar que el pedido aparece en la tabla.
    expect(
        page.locator("#ordersTable")
    ).to_contain_text(nombre_cliente)

    expect(
        page.locator("#ordersTable")
    ).to_contain_text(nombre_producto)

    # Comprobar que se actualizan los indicadores.
    expect(page.locator("#totalProductos")).to_have_text("1")
    expect(page.locator("#totalPedidos")).to_have_text("1")
    expect(page.locator("#pedidosCompletados")).to_have_text("1")
