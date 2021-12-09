#C:\Users\akayunov\AppData\Local\Programs\Python\Python39\python.exe C:\Users\akayunov\idle_work.py

import mouse
#import keyboard
import time
#while True:
while True:
    time.sleep(1)
    #keyboard.write('a')
    #keyboard.press('enter')
    #x = input(f'{time.time()}:dir=')
    mouse.move(10, 10, absolute=False, duration=0)
    time.sleep(1)
    print(time.time())
    mouse.move(-10, -10, absolute=False, duration=0)