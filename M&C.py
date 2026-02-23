import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import time
import math
from collections import deque

def encontrar_ventana_juego(titulo_parcial="Misioneros"):
    ventanas = gw.getAllWindows()
    for v in ventanas:
        if titulo_parcial.lower() in v.title.lower():
            return v
    return None

def abrir_y_enfocar_ventana(titulo_parcial="Misioneros", espera=1.0):
    print(f"Buscando ventana con título que contenga: '{titulo_parcial}'...")
    ventana = encontrar_ventana_juego(titulo_parcial)
    if ventana is None:
        print("No se encontró ninguna ventana con ese título.")
        return None
    print(f"Ventana encontrada: '{ventana.title}'")
    if ventana.isMinimized:
        ventana.restore()
        time.sleep(espera)
    ventana.activate()
    time.sleep(espera)
    return ventana

class MCAnalyzer:
    def __init__(self):
        self.frame = None
        self.canvas_bbox = None
        
        self.tpl_miss = cv2.imread("Assets/missionary.png", cv2.IMREAD_COLOR)
        self.tpl_cann = cv2.imread("Assets/cannibal.png", cv2.IMREAD_COLOR)
        
        if any(t is None for t in [self.tpl_miss, self.tpl_cann]):
            print("ERROR: Faltan las imágenes de plantilla (missionary.png o cannibal.png).")

    def calibrar_canvas(self):
        print("Buscando el lienzo del juego en la pantalla...")
        screenshot = pyautogui.screenshot()
        frame_full = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        hsv = cv2.cvtColor(frame_full, cv2.COLOR_BGR2HSV)

        lower_purple = np.array([120, 30, 30])
        upper_purple = np.array([160, 255, 120])
        mask_purple = cv2.inRange(hsv, lower_purple, upper_purple)

        lower_green = np.array([40, 40, 30])
        upper_green = np.array([85, 255, 180])
        mask_green = cv2.inRange(hsv, lower_green, upper_green)

        mask = cv2.bitwise_or(mask_purple, mask_green)

        kernel = np.ones((15, 15), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contornos:
            return False

        candidatos = [c for c in contornos if cv2.contourArea(c) > 100_000]
        if not candidatos:
            return False

        mejor = max(candidatos, key=cv2.contourArea)
        self.canvas_bbox = cv2.boundingRect(mejor)
        
        x, y, w, h = self.canvas_bbox
        print(f"¡Juego anclado exitosamente en: X:{x}, Y:{y} (Tamaño {w}x{h})!")
        return True

    def update(self):
        if self.canvas_bbox is None:
            if not self.calibrar_canvas():
                return False
        x, y, w, h = self.canvas_bbox
        img = pyautogui.screenshot(region=(x, y, w, h))
        self.frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return True

    def detect_boat(self):
        hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        lower_brown = np.array([5, 80, 50])
        upper_brown = np.array([20, 255, 255])
        mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)

        h_img, w_img = self.frame.shape[:2]
        mask_brown[0:int(h_img * 0.50), :] = 0

        contornos, _ = cv2.findContours(mask_brown, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contornos:
            return None

        candidatos = [c for c in contornos if cv2.contourArea(c) > 1500]
        if not candidatos:
            return None

        mejor_balsa = max(candidatos, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(mejor_balsa)
        return (x + w // 2, y + h // 2)

    def detect_entities(self, template, threshold=0.45):
        gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        gray_tpl = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        res = cv2.matchTemplate(gray_frame, gray_tpl, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(res >= threshold)
        
        th, tw = template.shape[:2]
        puntos_encontrados = []
        
        for x, y in zip(xs, ys):
            cx, cy = x + tw // 2, y + th // 2
            duplicado = False
            for px, py in puntos_encontrados:
                if math.hypot(cx - px, cy - py) < 30:
                    duplicado = True
                    break
            if not duplicado:
                puntos_encontrados.append((cx, cy))
        return puntos_encontrados

    def analizar_estado_unico(self, silencioso=False):
        if not self.update():
            return None
            
        boat_pos = self.detect_boat()
        missionaries = self.detect_entities(self.tpl_miss)
        cannibals = self.detect_entities(self.tpl_cann)
        
        mitad_pantalla = self.frame.shape[1] // 2
        
        m_izq, m_der, m_bote = [], [], []
        c_izq, c_der, c_bote = [], [], []
        
        margen_x = 100
        margen_y_sup = 100
        margen_y_inf = 50
        
        for mx, my in missionaries:
            if boat_pos and (boat_pos[0] - margen_x <= mx <= boat_pos[0] + margen_x) and \
                            (boat_pos[1] - margen_y_sup <= my <= boat_pos[1] + margen_y_inf):
                m_bote.append((mx, my))
            elif mx < mitad_pantalla:
                m_izq.append((mx, my))
            else:
                m_der.append((mx, my))

        for cx, cy in cannibals:
            if boat_pos and (boat_pos[0] - margen_x <= cx <= boat_pos[0] + margen_x) and \
                            (boat_pos[1] - margen_y_sup <= cy <= boat_pos[1] + margen_y_inf):
                c_bote.append((cx, cy))
            elif cx < mitad_pantalla:
                c_izq.append((cx, cy))
            else:
                c_der.append((cx, cy))
                
        boat_side = "Desconocido"
        if boat_pos:
            boat_side = "Izquierda" if boat_pos[0] < mitad_pantalla else "Derecha"

        if not silencioso:
            print("\nAnálisis de Estado Completado:")
            print(f"   Orilla Izquierda : {len(m_izq)} M | {len(c_izq)} C")
            print(f"   Bote ({boat_side})   : {len(m_bote)} M | {len(c_bote)} C")
            print(f"   Orilla Derecha   : {len(m_der)} M | {len(c_der)} C")

        return {
            "bote_pos": boat_pos,
            "bote": boat_side,
            "izq": {"M": m_izq, "C": c_izq},
            "abordo": {"M": m_bote, "C": c_bote},
            "der": {"M": m_der, "C": c_der}
        }

    def calcular_siguiente_movimiento(self, estado):
        if not estado or estado["bote"] == "Desconocido":
            return None

        lado_bote = estado["bote"]
        
        if lado_bote == "Izquierda":
            m_izq = len(estado["izq"]["M"]) + len(estado["abordo"]["M"])
            c_izq = len(estado["izq"]["C"]) + len(estado["abordo"]["C"])
        else:
            m_izq = len(estado["izq"]["M"])
            c_izq = len(estado["izq"]["C"])

        if (m_izq > 0 and m_izq < c_izq) or (3 - m_izq > 0 and 3 - m_izq < 3 - c_izq):
            print("¡Game Over detectado! Los caníbales son mayoría.")
            return None

        estado_inicial = (m_izq, c_izq, lado_bote)

        def es_valido(m, c):
            if m < 0 or c < 0 or m > 3 or c > 3: return False
            if m > 0 and m < c: return False
            if (3 - m) > 0 and (3 - m) < (3 - c): return False
            return True

        movimientos = [(1,0), (2,0), (0,1), (0,2), (1,1)]
        cola = deque([(estado_inicial, [])])
        visitados = set([estado_inicial])

        while cola:
            (m, c, bote), camino = cola.popleft()

            if m == 3 and c == 3 and bote == "Izquierda":
                return camino

            for dm, dc in movimientos:
                if bote == "Izquierda":
                    nuevo_m, nuevo_c = m - dm, c - dc
                    nuevo_bote = "Derecha"
                else:
                    nuevo_m, nuevo_c = m + dm, c + dc
                    nuevo_bote = "Izquierda"

                nuevo_estado = (nuevo_m, nuevo_c, nuevo_bote)

                if es_valido(nuevo_m, nuevo_c) and nuevo_estado not in visitados:
                    visitados.add(nuevo_estado)
                    cola.append((nuevo_estado, camino + [(dm, dc)]))
        return None

    def hacer_clic(self, cx, cy):
        """Hace clic rápido en la pantalla."""
        bx, by, _, _ = self.canvas_bbox
        pyautogui.moveTo(bx + cx, by + cy, duration=0.1) # Movimiento ágil del ratón
        pyautogui.click()
        time.sleep(0.2) # Breve pausa para que el juego registre el clic

    def jugar_automaticamente(self):
        paso_num = 1
        while True:
            time.sleep(1) # Pausa principal de 1 segundo
            estado = self.analizar_estado_unico()
            
            if not estado or estado["bote"] == "Desconocido":
                print("Bote no detectado claramente. Esperando 1 segundo...")
                continue

            lado = estado["bote"]

            # 1. ¿GANAMOS? Si todos están a la izquierda (y el bote vacío)
            if len(estado["izq"]["M"]) == 3 and len(estado["izq"]["C"]) == 3 and lado == "Izquierda":
                print("\n¡VICTORIA LOGRADA! El juego ha sido resuelto con éxito.")
                break

            # Limpieza de seguridad: Si arranca el turno y quedó alguien arriba, lo bajamos
            if len(estado["abordo"]["M"]) > 0 or len(estado["abordo"]["C"]) > 0:
                print("Bajando pasajeros rezagados...")
                for mx, my in estado["abordo"]["M"]: self.hacer_clic(mx, my)
                for cx, cy in estado["abordo"]["C"]: self.hacer_clic(cx, cy)
                time.sleep(1)
                continue

            # 2. PENSAR LA JUGADA
            camino = self.calcular_siguiente_movimiento(estado)
            # if not camino:
            #     print("No encontré un camino válido. Posible Game Over o error de detección.")
            #     break

            siguiente_mov = camino[0]
            m_a_subir, c_a_subir = siguiente_mov[0], siguiente_mov[1]

            print("-" * 50)
            print(f"PASO {paso_num}: Subir {m_a_subir} Misioneros y {c_a_subir} Caníbales. Cruzar a la {'Derecha' if lado == 'Izquierda' else 'Izquierda'}.")

            # 3. SUBIR PASAJEROS
            orilla = "izq" if lado == "Izquierda" else "der"
            for i in range(m_a_subir):
                mx, my = estado[orilla]["M"][i]
                self.hacer_clic(mx, my)
                
            for i in range(c_a_subir):
                cx, cy = estado[orilla]["C"][i]
                self.hacer_clic(cx, cy)

            time.sleep(1) # Un segundo para que los personajes terminen de saltar al bote

            # 4. HACER CLIC EN EL BOTE PARA CRUZAR
            print("Cruzando el río...")
            estado_listo = self.analizar_estado_unico(silencioso=True) # Foto silenciosa para ubicar el bote con precisión
            if estado_listo and estado_listo["bote_pos"]:
                bx, by = estado_listo["bote_pos"]
                self.hacer_clic(bx, by)
            else:
                bx, by = estado["bote_pos"]
                self.hacer_clic(bx, by)
            
            # 5. ESPERAR A QUE LLEGUE AL OTRO LADO Y BAJAR PASAJEROS INMEDIATAMENTE
            llegado = False
            intentos = 0
            while not llegado and intentos < 10:
                time.sleep(1) # Chequear cada 1 segundo
                intentos += 1
                
                # Tomamos fotos silenciosas para no llenar la consola de texto
                estado_llegada = self.analizar_estado_unico(silencioso=True) 
                
                # Si el bote vuelve a ser visible y cambió de lado... ¡Llegamos!
                if estado_llegada and estado_llegada["bote"] != "Desconocido" and estado_llegada["bote"] != lado:
                    llegado = True
                    print("Bote en destino. Bajando pasajeros a tierra firme...")
                    
                    for mx, my in estado_llegada["abordo"]["M"]:
                        self.hacer_clic(mx, my)
                    for cx, cy in estado_llegada["abordo"]["C"]:
                        self.hacer_clic(cx, cy)
                        
            paso_num += 1

if __name__ == "__main__":
    ventana = abrir_y_enfocar_ventana(titulo_parcial="Misioneros")
    if ventana is None:
        print("\nNo se pudo encontrar la ventana. Asegúrate de tener el juego abierto.")
        exit(1)

    analyzer = MCAnalyzer()
    analyzer.jugar_automaticamente()