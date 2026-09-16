
برای راه اندازی چند کانال تونل و بالانسر با HA Proxy


### روی سرور ایران و خارج

با گرینه 1 - پیش نیاز ها رو روی سرور خارج و ایران انجام میدیم

```
1. Nasb Dependencies va FRP v0.71.0
```


با گزینه 9 - بهینه سازی های سرور رو انجام میدیم


```
9. Optimize System (TCP/BBR ya UDP)

```
بعد گزینه 3 رو انتخاب میکنیم

```
1) Optimize for TCP / WebSocket (BBR + large TCP buffers)
2) Optimize for KCP / QUIC (UDP buffers)
3) Both + Extra high-BW tweaks
Select:

```

----

### روی سرور ایران


روی سرور ایران منوی 10 رو انتخاب میکنیم

```
10. Aggregation Multi-Tunnel ba HAProxy (Bandwidth bala)
```


<img width="593" height="467" alt="image" src="https://github.com/user-attachments/assets/b9bdd618-6121-447c-b73d-9c15f9e68e09" />

---


```
Samt:
  1) Iran  (frps + HAProxy + ghavanin routing)  ← AVVAL inja
  2) Kharej (frpc)  ← baad, line-haye compact az Iran ra paste kon
Select [1-2]:
```

شماره 1 رو انتخاب میکنم که سرور ایران رو راه اندازی کنیم


توی قسمت بعدی ازمون مشخصات کانال ( تونل) ها رو میخواد

```
=== Tunnel Protocol Preset ===
Noe ertebat control FRP (TCP/WS/KCP). Traffic Xray hamishe TCP proxy ast.
  1) All TCP x4      — sadeh/paydar (pishnahad Xray gRPC)
  2) 2x TCP + 2x WS  — nime TCP, nime WebSocket
  3) Mix TCP + WS    — tedad dasti
  4) N x WebSocket   — faghat WS
  5) N x KCP         — bar asase UDP
  6) N x TCP only    — tedad TCP (1-8)
  7) Custom mix      — TCP + WS + KCP
Mesal: 4 tunnel TCP baraye bandwidth → gozine 1
Select preset [1-7]:
````



من میخوام 6 تا تونل داشته باشم، 3 تاش tcp باشه و 3 تای دیگه web socket

گزینه سوم رو انتخاب میکنم


```
3) Mix TCP + WS    — tedad dasti
```

ارم تعداد تانل های tcp رو میخواد

```
TCP count:
``

3 رو وارد میکنم

بعد ازم تعداد کانال های وب سوکت رو میخواد، اونم 3 رو وارد میکنم

```
WebSocket count:
```

----


توی مرحله بعدی ازتون میپرسه که شماره کانفیگ ها از چند شروع بشه؟

```

--- Base Tunnel Index ---
Shomare shoroo'e tunnel-ha (poshte sar ham).
  Mesal: base=1 va 4 tunnel → ID-ha: 1,2,3,4
  Mesal: base=5 va 2 tunnel → ID-ha: 5,6
Agar ghablan tunnel 1-3 dari, base ra 4 begzar ta conflict nashe.
Base Tunnel Index (1-10) [1]: 

```

من چون از قبل تانلی ندارم روی این سرور میتونم از شماره 1 وارد کنم تا شماره 4، چون محدودیت این اسکریپت برای 10 تانل هست


عدد 4 رو وارد میکنم



در این مرحله اسکریپت شروع میکنه به ساخت تانل ها

---

در قسمت بعدی از شما شماره پورتی که میخواید ترافیک VPN ازش رد بشه رو میپرسه، باید همون پورت کانفیگ روی سرور خارجتون رو وارد کنید

برای من 443 هست

```
=== HAProxy Routing (yeki balanser per port) ===
Har public port = yek frontend + yek backend joda.
Client be an port mizanad; HAProxy beyne tunnel-haye an port load-balance mikonad.

Mesal:
  Port 443  + tunnels all  → balanser baraye Xray asli
  Port 2053 + tunnels all  → balanser joda baraye inbound digar
  Port 2090 + tunnels 1,2  → faghat 2 tunnel

Tunnel IDs: benevis all ya Enter = hame tunnel-ha
Port khali = payan.

--- Balancer #1 ---
Public port (e.g. 443) ya khali=payan: 
```


---

در قدم بعدی میپرسه میخواد این ترافیک 443 از کدوم کانال (تانل) ها رد بشه، all رو تایپ میکنم و Enter رو میزنم


```
--- Balancer #1 ---
Public port (e.g. 443) ya khali=payan: 443
Tunnel-ha (all / Enter / 1,2,3): available=[4,5,6,7,8,9]
```

در قسمت بعدی که ازم میپرسه ، میگم پورت دیگه ای نمیخوام فوروارد بشه، و بدون وارد کردن هیچ مقداری Enter رو میزنم

```
--- Balancer #1 ---
Public port (e.g. 443) ya khali=payan: 443
Tunnel-ha (all / Enter / 1,2,3): available=[4,5,6,7,8,9]all  
  + balanser :443 → tunnels [4,5,6,7,8,9]
--- Balancer #2 ---
Public port (e.g. 443) ya khali=payan:    
```

---
در قدم بعدی تمامی مشخصات مربوط به این تانل ها و کانفیگ ها رو بهتون نشون میده

مثل نوشته زیر


```
================ IRAN SIDE AGGREGATION READY ================
Server IP            : 5.25.17.25

Active routing rules:
  Rule 1: ports [443] → tunnels [4,5,6,7,8,9]

========== COPY THESE LINES TO KHAREJ (option 10 → side 2) ==========
# Format: ID,protocol,bindPort,token,remotePort,iperfRemotePort
4,tcp,57909,nZdawJt9GmnFUTaq,20400,21400
5,tcp,46175,rZdJtnGMYnFUymoi,20401,21401
6,tcp,42109,jZdJt9GMYghfgTai,20402,21402
7,ws,41076,oZdJt9GMYndyasdf,20403,21403
8,ws,46759,qZdJt9GMdYnszcvai,20404,21404
9,ws,46192,sZdJt9GsMYnFupak,20405,21405

====================================================================

Saved: /etc/frp/aggregation_4_compact.txt
Rules: /etc/frp/aggregation_4_rules.conf
You can change routing later from menu option 11.

Press Enter to return...
```



----


###روی سرور خارج




