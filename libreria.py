# --- EXCEPCIONES PERSONALIZADAS ---
class ErrorISBNduplicado(Exception):
    pass

class LibroNoEncontradoError(Exception):
    pass

class SinStockError(Exception):
    pass

class PrestamoActivoNoEncontradoError(Exception):
    pass


class Libro:
    def __init__(self, isbn: str, titulo: str, autor: str, stock: int = 1):
        # 1. Validación de tipos y cadenas vacías
        if not isinstance(isbn, str) or not isbn.strip():
            raise ValueError("El ISBN no puede estar vacío.")
        if not isinstance(titulo, str) or not titulo.strip():
            raise ValueError("El título no puede estar vacío.")
        if not isinstance(autor, str) or not autor.strip():
            raise ValueError("El autor no puede estar vacío.")

        # 2. Validación de ISBN: mínimo 8 números (se cuentan solo los dígitos)
        isbn_limpio = isbn.strip()
        digitos_isbn = "".join(filter(str.isdigit, isbn_limpio))
        if len(digitos_isbn) < 8:
            raise ValueError("El ISBN debe contener al menos 8 números.")

        # 3. Validación de Autor: no debe admitir números
        autor_limpio = autor.strip()
        if any(c.isdigit() for c in autor_limpio):
            raise ValueError("El nombre del autor no debe contener números.")

        # 4. Validación estricta de Stock (evita booleanos y flotantes)
        if isinstance(stock, bool) or not isinstance(stock, int) or stock <= 0:
            raise ValueError("El stock inicial debe ser un número entero mayor a 0.")

        self._isbn = isbn_limpio
        self.titulo = titulo.strip()
        self.autor = autor_limpio
        self._stock = stock

    @property
    def isbn(self) -> str:
        # Protege el ISBN para que no sea alterado después de crear el libro
        return self._isbn

    @property
    def stock(self) -> int:
        return self._stock

    @stock.setter
    def stock(self, valor: int):
        # Impide que se asigne stock negativo o tipos inválidos desde fuera
        if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
            raise ValueError("El stock debe ser un número entero mayor o igual a 0.")
        self._stock = valor

    def __eq__(self, otro):
        if isinstance(otro, Libro):
            return self._normalizar_isbn(self.isbn) == self._normalizar_isbn(otro.isbn)
        return False

    @staticmethod
    def _normalizar_isbn(isbn: str) -> str:
        """Elimina guiones y espacios para evitar duplicados disfrazados."""
        return "".join(c for c in isbn if c.isalnum()).lower()


class CatalogoLibros:
    def __init__(self):
        self._libros = {}  # Clave: ISBN normalizado, Valor: Objeto Libro

    def agregar_libro(self, libro: Libro):
        if not isinstance(libro, Libro):
            raise TypeError("Solo se pueden agregar instancias de la clase Libro.")

        clave_isbn = Libro._normalizar_isbn(libro.isbn)
        if clave_isbn in self._libros:
            raise ErrorISBNduplicado(f"El libro con ISBN {libro.isbn} ya existe.")
        self._libros[clave_isbn] = libro

    def buscar_por_isbn(self, isbn: str) -> Libro:
        if not isinstance(isbn, str) or not isbn.strip():
            raise LibroNoEncontradoError("Debe proporcionar un ISBN válido.")

        clave_isbn = Libro._normalizar_isbn(isbn)
        if clave_isbn not in self._libros:
            raise LibroNoEncontradoError(f"No se encontró ningún libro con el ISBN {isbn.strip()}.")
        return self._libros[clave_isbn]

    def buscar(self, consulta: str) -> list:
        if not isinstance(consulta, str) or not consulta.strip():
            return []

        consulta_limpia = consulta.strip().lower()
        consulta_isbn = Libro._normalizar_isbn(consulta_limpia)
        resultados = []

        for libro in self._libros.values():
            coincide_texto = (
                consulta_limpia in libro.titulo.lower()
                or consulta_limpia in libro.autor.lower()
                or consulta_limpia in libro.isbn.lower()
            )
            coincide_isbn_norm = bool(consulta_isbn) and (
                consulta_isbn in Libro._normalizar_isbn(libro.isbn)
            )

            if coincide_texto or coincide_isbn_norm:
                resultados.append(libro)
        return resultados

    def obtener_todos_los_libros(self) -> list:
        return list(self._libros.values())


class GestorPrestamos:
    def __init__(self, catalogo: CatalogoLibros):
        self.catalogo = catalogo
        self._prestamos_activos = {}  # Clave: ISBN normalizado, Valor: cantidad prestada

    def prestar_libro(self, isbn: str):
        libro = self.catalogo.buscar_por_isbn(isbn)
        if libro.stock <= 0:
            raise SinStockError(f"El libro '{libro.titulo}' no tiene stock disponible.")

        clave_isbn = Libro._normalizar_isbn(libro.isbn)
        libro.stock -= 1
        self._prestamos_activos[clave_isbn] = self._prestamos_activos.get(clave_isbn, 0) + 1

    def devolver_libro(self, isbn: str):
        libro = self.catalogo.buscar_por_isbn(isbn)
        clave_isbn = Libro._normalizar_isbn(libro.isbn)

        if clave_isbn not in self._prestamos_activos or self._prestamos_activos[clave_isbn] <= 0:
            raise PrestamoActivoNoEncontradoError(f"No hay registros de préstamos activos para el ISBN {isbn.strip()}.")

        libro.stock += 1
        self._prestamos_activos[clave_isbn] -= 1
        if self._prestamos_activos[clave_isbn] == 0:
            del self._prestamos_activos[clave_isbn]

    def obtener_prestamos_activos(self) -> dict:
        # Devuelve una copia para evitar mutaciones accidentales desde el exterior
        return self._prestamos_activos.copy()


class GeneradorReportes:
    def __init__(self, catalogo: CatalogoLibros, gestor_prestamos: GestorPrestamos):
        self.catalogo = catalogo
        self.gestor_prestamos = gestor_prestamos

    def resumen_inventario(self) -> dict:
        libros = self.catalogo.obtener_todos_los_libros()
        total_titulos = len(libros)
        total_copias = sum(libro.stock for libro in libros)
        prestamos = sum(self.gestor_prestamos.obtener_prestamos_activos().values())
        return {
            "total_titulos": total_titulos,
            "copias_disponibles": total_copias,
            "prestamos_activos": prestamos
        }


def main():
    catalogo = CatalogoLibros()
    gestor_prestamos = GestorPrestamos(catalogo)
    generador_reportes = GeneradorReportes(catalogo, gestor_prestamos)

    # Datos de prueba iniciales
    try:
        catalogo.agregar_libro(Libro("978-0132350884", "Clean Code", "Robert C. Martin", 2))
        catalogo.agregar_libro(Libro("978-0201633610", "Design Patterns", "Erich Gamma", 1))
    except (ValueError, ErrorISBNduplicado) as e:
        print(f"Advertencia al cargar datos iniciales: {e}")

    while True:
        print("\n=== SISTEMA DE GESTIÓN DE BIBLIOTECA (MVP) ===")
        print("1. Registrar libro")
        print("2. Buscar libros (Catálogo)")
        print("3. Prestar libro")
        print("4. Devolver libro")
        print("5. Ver reporte simple")
        print("6. Salir")

        try:
            opcion = input("\nSelecciona una opción (1-6): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo del sistema. ¡Hasta luego!")
            break

        if opcion == "1":
            try:
                isbn = input("ISBN (mínimo 8 números): ").strip()
                titulo = input("Título: ").strip()
                autor = input("Autor (No acepta números): ").strip()
                stock_str = input("Stock inicial (Siempre mayor a 0): ").strip()

                if not stock_str.isdigit():
                    raise ValueError("El stock debe ser un número entero positivo.")
                stock = int(stock_str)

                catalogo.agregar_libro(Libro(isbn, titulo, autor, stock))
                print("¡Libro registrado exitosamente!")
            except ValueError as e:
                print(f"Error de validación: {e}")
            except ErrorISBNduplicado as e:
                print(f"Error: {e}")

        elif opcion == "2":
            consulta = input("Ingresa término de búsqueda (título, autor o ISBN): ").strip()
            if not consulta:
                print("Error: Debes ingresar al menos un carácter para buscar.")
                continue

            resultados = catalogo.buscar(consulta)
            if not resultados:
                print("No se encontraron coincidencias.")
            else:
                print(f"\nSe encontraron {len(resultados)} resultados:")
                for b in resultados:
                    print(f" - [{b.isbn}] '{b.titulo}' por {b.autor} | Stock disponible: {b.stock}")

        elif opcion == "3":
            isbn = input("Ingresa el ISBN del libro a prestar: ").strip()
            try:
                gestor_prestamos.prestar_libro(isbn)
                print("¡Préstamo registrado con éxito!")
            except (LibroNoEncontradoError, SinStockError) as e:
                print(f"Error: {e}")

        elif opcion == "4":
            isbn = input("Ingresa el ISBN del libro a devolver: ").strip()
            try:
                gestor_prestamos.devolver_libro(isbn)
                print("¡Devolución registrada con éxito!")
            except (LibroNoEncontradoError, PrestamoActivoNoEncontradoError) as e:
                print(f"Error: {e}")

        elif opcion == "5":
            resumen = generador_reportes.resumen_inventario()
            print("\n--- REPORTE DE ESTADO DE LA BIBLIOTECA ---")
            print(f"Títulos diferentes registrados: {resumen['total_titulos']}")
            print(f"Ejemplares disponibles en stock: {resumen['copias_disponibles']}")
            print(f"Préstamos activos actuales: {resumen['prestamos_activos']}")

        elif opcion == "6":
            print("Saliendo del sistema. ¡Hasta luego!")
            break
        else:
            print("Opción inválida, por favor elige un número del 1 al 6.")


if __name__ == "__main__":
    main()