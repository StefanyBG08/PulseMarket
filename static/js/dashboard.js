
const money = value =>
    new Intl.NumberFormat("es-MX", {
        style: "currency",
        currency: "MXN",
        maximumFractionDigits: 2
    }).format(value);

async function getJSON(url, options = {}) {
    const response = await fetch(url, options);

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.error || "No se pudo obtener la información.");
    }

    return response.json();
}

async function cargarEstadisticas() {
    const stats = await getJSON("/api/stats");

    document.getElementById("totalVentas").textContent =
        money(stats.ventas_totales);

    document.getElementById("totalPedidos").textContent =
        stats.total_pedidos;

    document.getElementById("totalProductos").textContent =
        stats.total_productos;

    document.getElementById("pedidosCompletados").textContent =
        stats.pedidos_completados;

    crearGrafica(stats.ventas_mensuales);
}

function crearGrafica(ventas) {
    const canvas = document.getElementById("salesChart");

    if (window.salesChartInstance) {
        window.salesChartInstance.destroy();
    }

    window.salesChartInstance = new Chart(canvas, {
        type: "line",
        data: {
            labels: [
                "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
            ],
            datasets: [{
                label: "Ventas",
                data: ventas,
                borderColor: "#a78bfa",
                backgroundColor: "rgba(139, 92, 246, 0.15)",
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointRadius: 3,
                pointBackgroundColor: "#a78bfa"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: context => money(context.raw)
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: "#8e9bb5" }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(142, 155, 181, 0.12)" },
                    ticks: {
                        color: "#8e9bb5",
                        callback: value => "$" + value.toLocaleString("es-MX")
                    }
                }
            }
        }
    });
}

async function cargarProductos() {
    const productos = await getJSON("/api/productos");
    const tabla = document.getElementById("productsTable");
    const inventario = document.getElementById("inventoryList");

    tabla.innerHTML = "";
    inventario.innerHTML = "";

    productos.forEach(producto => {
        const fila = document.createElement("tr");

        [
            producto.id,
            producto.nombre,
            producto.categoria,
            money(producto.precio),
            producto.stock
        ].forEach(valor => {
            const celda = document.createElement("td");
            celda.textContent = valor;
            fila.appendChild(celda);
        });

        tabla.appendChild(fila);
    });

    const maxStock = Math.max(...productos.map(p => p.stock), 1);

    productos.slice(0, 5).forEach(producto => {
        const porcentaje = Math.min(
            100,
            Math.round(producto.stock / maxStock * 100)
        );

        const item = document.createElement("div");
        item.className = "inventory-item";

        const info = document.createElement("div");
        info.className = "inventory-info";

        const nombre = document.createElement("span");
        nombre.textContent = producto.nombre;

        const cantidad = document.createElement("span");
        cantidad.textContent = producto.stock + " unidades";

        info.append(nombre, cantidad);

        const barra = document.createElement("div");
        barra.className = "progress";

        const relleno = document.createElement("div");
        relleno.className = "progress-bar";
        relleno.style.width = porcentaje + "%";

        barra.appendChild(relleno);
        item.append(info, barra);
        inventario.appendChild(item);
    });

    if (productos.length === 0) {
        inventario.textContent = "No hay productos registrados.";
    }
}

async function cargarPedidos() {
    const pedidos = await getJSON("/api/pedidos");
    const tabla = document.getElementById("ordersTable");

    tabla.innerHTML = "";

    pedidos.forEach(pedido => {
        const fila = document.createElement("tr");

        const valores = [
            pedido.id,
            pedido.cliente,
            pedido.producto,
            money(pedido.total)
        ];

        valores.forEach((valor, index) => {
            const celda = document.createElement("td");
            celda.textContent = valor;

            if (index === 0) {
                celda.className = "order-id";
            }

            fila.appendChild(celda);
        });

        const celdaEstado = document.createElement("td");
        const etiqueta = document.createElement("span");
        etiqueta.className =
            "state state-" + pedido.estado.toLowerCase().replaceAll(" ", "-");
        etiqueta.textContent = pedido.estado;

        celdaEstado.appendChild(etiqueta);
        fila.appendChild(celdaEstado);
        tabla.appendChild(fila);
    });
}

async function actualizarDashboard() {
    const mensaje = document.getElementById("formMessage");

    try {
        await Promise.all([
            cargarEstadisticas(),
            cargarProductos(),
            cargarPedidos()
        ]);
    } catch (error) {
        console.error(error);
        mensaje.textContent =
            "No se pudo cargar algún dato. Comprueba que Flask esté ejecutándose.";
        mensaje.style.color = "#f87171";
    }
}

document.getElementById("productForm").addEventListener("submit", async event => {
    event.preventDefault();

    const formulario = event.currentTarget;
    const datos = Object.fromEntries(new FormData(formulario).entries());

    datos.precio = Number(datos.precio);
    datos.stock = Number(datos.stock);

    const mensaje = document.getElementById("formMessage");

    try {
        await getJSON("/api/productos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });

        formulario.reset();
        mensaje.textContent = "Producto agregado correctamente.";
        mensaje.style.color = "#34d399";

        await actualizarDashboard();
    } catch (error) {
        mensaje.textContent = error.message;
        mensaje.style.color = "#f87171";
    }
});


document.getElementById("orderForm").addEventListener("submit", async event => {
    event.preventDefault();

    const formulario = event.currentTarget;
    const datos = Object.fromEntries(new FormData(formulario).entries());

    datos.total = Number(datos.total);

    const mensaje = document.getElementById("formMessage");

    try {
        await getJSON("/api/pedidos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });

        formulario.reset();

        mensaje.textContent = "Pedido registrado correctamente.";
        mensaje.style.color = "#34d399";

        await actualizarDashboard();
    } catch (error) {
        mensaje.textContent = error.message;
        mensaje.style.color = "#f87171";
    }
});


document.getElementById("refreshButton").addEventListener(
    "click",
    actualizarDashboard
);

document.getElementById("themeToggle").addEventListener("click", () => {
    document.body.classList.toggle("light-theme");
});

document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", () => {
        document.querySelectorAll(".nav-link").forEach(item => {
            item.classList.remove("active");
        });

        link.classList.add("active");
    });
});

actualizarDashboard();
