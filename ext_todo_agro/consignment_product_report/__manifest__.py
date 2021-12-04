# -*- coding: utf-8 -*-

{
    "name":"Reporte consignación de productos",
    "description":"Añade wizard para generar reporte de productos con consignación entre rango de fechas en Inventario/Informes.",
    "author":"Christopher García",
    "depends":['stock','account'],
    "data":[
        'views/wizards_consignment_product.xml',
        'reports/report_consignment_product.xml',
         'security/security.xml'
    ]
}