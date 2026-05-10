# -*- coding: utf-8 -*-
"""teclador_f.py

Script auxiliar (Windows) que:
- roda e fica aguardando teclas
- ao pressionar F (case-insensitive para detectar, mas digita case-sensitively),
  digita caractere por caractere a string VALUE
- respeita case ao digitar (usa os caracteres exatamente como estão em VALUE)

Parar com ESC.

Requisitos:
  pip install pyautogui keyboard

Observação:
- Este script usa automação de teclado. Use com cuidado.
"""

import time

VALUE = "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"


def main():
    import keyboard
    import pyautogui

    # Evita que pyautogui pause entre caracteres (vamos controlar com sleep)
    pyautogui.PAUSE = 0

    print("[teclador_f] Pronto. Pressione 'F' para digitar. Pressione 'ESC' para sair.")

    # Pequeno delay para garantir foco na janela desejada
    startup_delay = 0.15

    def type_value_char_by_char():
        time.sleep(startup_delay)
        # Digita caractere por caractere, preservando case exatamente como VALUE
        for ch in VALUE:
            pyautogui.typewrite(ch, interval=0)  # sem intervalo interno
            # intervalo manual para consistência
            time.sleep(0.01)

    # Fica escutando teclas
    keyboard.add_hotkey('f', type_value_char_by_char, suppress=False, trigger_on_release=False)
    keyboard.wait('esc')


if __name__ == "__main__":
    main()

