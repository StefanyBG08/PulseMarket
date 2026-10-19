
import os
import pytest

# Impide ejecutar las pruebas contra una base de datos distinta
# de la base exclusiva de pruebas.
if os.getenv("DB_NAME") != "pulsemarket_test":
    raise RuntimeError(
        "Pruebas canceladas: configura DB_NAME=pulsemarket_test "
        "antes de ejecutarlas. No se permiten pruebas contra producción."
    )

from app import app as flask_app, conectar_db, inicializar_db


@pytest.fixture()
def cliente():
    with conectar_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS pedidos;")
            cursor.execute("DROP TABLE IF EXISTS productos;")
        conexion.commit()

    inicializar_db()
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client

    with conectar_db() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS pedidos;")
            cursor.execute("DROP TABLE IF EXISTS productos;")
        conexion.commit()


def test_pagina_principal(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200


def test_listar_productos(cliente):
    respuesta = cliente.get("/api/productos")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == []


def test_registrar_producto(cliente):
    respuesta = cliente.post(
        "/api/productos",
        json={
            "nombre": "Producto de prueba",
            "categoria": "Accesorios",
            "precio": 350,
            "stock": 10,
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["nombre"] == "Producto de prueba"

    listado = cliente.get("/api/productos").get_json()
    assert len(listado) == 1
    assert listado[0]["nombre"] == "Producto de prueba"


def test_registrar_pedido(cliente):
    respuesta = cliente.post(
        "/api/pedidos",
        json={
            "cliente": "Cliente de prueba",
            "producto": "Producto de prueba",
            "total": 350,
            "estado": "Pendiente",
        },
    )

    assert respuesta.status_code == 201
    pedido = respuesta.get_json()
    assert pedido["cliente"] == "Cliente de prueba"
    assert pedido["estado"] == "Pendiente"
    assert pedido["id"].startswith("PED-")


def test_rechazar_pedido_con_total_cero(cliente):
    respuesta = cliente.post(
        "/api/pedidos",
        json={
            "cliente": "Cliente de prueba",
            "producto": "Producto de prueba",
            "total": 0,
            "estado": "Pendiente",
        },
    )

    assert respuesta.status_code == 400
    assert "error" in respuesta.get_json()


def test_estadisticas(cliente):
    cliente.post(
        "/api/productos",
        json={
            "nombre": "Teclado",
            "categoria": "Accesorios",
            "precio": 350,
            "stock": 10,
        },
    )

    cliente.post(
        "/api/pedidos",
        json={
            "cliente": "Cliente de prueba",
            "producto": "Teclado",
            "total": 350,
            "estado": "Completado",
        },
    )

    respuesta = cliente.get("/api/stats")
    assert respuesta.status_code == 200

    datos = respuesta.get_json()
    assert datos["total_productos"] == 1
    assert datos["total_pedidos"] == 1
    assert datos["ventas_totales"] == 350
    assert datos["pedidos_completados"] == 1
    assert len(datos["ventas_mensuales"]) == 12
