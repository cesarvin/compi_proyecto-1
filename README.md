
# 🧪 Fase 1 Proyecto: Compilador para Compiscript

- **César Vinicio Rodas Alvarado**
- **16776**

## 📋 Descripción General

Primera fase del desarrollo de un compilador para el lenguaje CompiScript.

En esta fase se implementan el analizador léxico y el analizador sintáctico utilizando la herramienta ANTLR en Python. Además, se completa el desarrollo del analizador semántico.

Como resultado, se obtiene un código que es válido conforme a la gramática de CompiScript, y se genera la tabla de símbolos y tipos, la cual servirá como base para las siguientes fases del desarrollo del compilador.

---

## 🧰 Instrucciones de Configuración

En la carpeta compiscript:

1. **Construir y Ejecutar el Contenedor Docker:** Desde el directorio raíz, ejecuta el siguiente comando para construir la imagen y lanzar un contenedor interactivo:

   ```bash
   docker build --rm . -t csp-image && docker run --rm -ti -v "$(pwd)/program":/program csp-image
   ```

   Con esta instrucción se crea una imagen de docker que contine todo el codigo del compilador. 
   
2. **Establecer el Entorno**

   - El directorio `program` se monta dentro del contenedor.
   - Este contiene:
      - **gramática de ANTLR de Compiscript y una versión en BNF**
      - Visitors nesarios para hacer el analisis
      - Un archivo `Driver.py` (punto de entrada principal) 
      - `program.cps` (entrada de prueba con la extensión de archivos de Compiscript). Pueden agregarse otros archivos con extensión .csp si fuera necesario. 
      - Una carpeta con Recursos. Las tablas y configuraciones necesarias para el sistema. 
      - Un archivo app.py que es el archivo con el que se crea el api para poder consumir el recurso en la maquina host. 
      - Un archivo test_compilador.py con una serie de pruebas para poder ejectuar pruebas unitarias sobre el compilador. 

    - En el directorio raiz se encuentran los archivos:
      - Dockerfile, necesario para establecer el ambiente de docker. 
      - docker-compose.yml necesario para levantar el ambiente del api. 

3. **Levantar el api:** En otra ventana de la terminal, desde la carpeta raíz, ejecuta el siguiente comando para levantar el api. 

   ```bash
   docker compose up
   ```

4. **Probar el funcionamiento del api**
   Desde el navegador de la computadora Host ingresar a:

   ```bash
   http://localhost:8000/
   ```
  se muestra una pagina que indica que el Api esta funcionando con el mensaje: API compilador Compiscript funcionando!
   

---

## ✅ USOS

1. **Usar en la terminal:** Una vez levantado el habiente del docker, en la terminal se muestra directamente la ruta 

    ```bash
    rootdokcer@hash:/program#
    ```

    En esta terminal se puede usar el driver directamente para analizar un archivo, con la siguiente instrucción:

    Usa el driver para analizar el archivo de prueba:

   ```bash
   python3 Driver.py program.cps
   ```

2. **Ejecutar pruebas unitarias** Una vez levantado el habiente del docker, en la terminal se muestra directamente la ruta 

    ```bash
    rootdokcer@hash:/program#
    ```

    Para ejecutar las pruebas, en esta terminal escribir el siguiente comando:

   ```bash
   python3 -m unittest test_compilador.py
   ```

3. **Editor Compiscript v1.0** En la maquina host, dentro de la carpeta editor hay un archivo llamado editor.py

    Para poder ejecutar el editor es necesario tener instalada la librería TK en la maquina host, en linux puede usar este comando:

   ```bash
   sudo apt-get install python3-tk
   ```

    Para ejecutar el editor se debe escribir el siguiente comando

   ```bash
   python3 editor.py
   ```

   
