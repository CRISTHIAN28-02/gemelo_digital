# ==============================================================================
# REGISTRO DE AUDITORÍA — se llama tras cada acción relevante del sistema.
# ==============================================================================

from datetime import datetime

from database import db


def registrar_evento(usuario: str, accion: str, modulo: str, resultado: str = "Éxito",
                      descripcion: str = ""):
    db.ejecutar(
        """INSERT INTO auditoria (usuario, fecha, accion, modulo, descripcion, resultado)
           VALUES (?,?,?,?,?,?)""",
        (usuario, datetime.now().isoformat(timespec="seconds"), accion, modulo, descripcion, resultado),
    )
