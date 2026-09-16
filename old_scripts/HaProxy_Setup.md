
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
از منوی 9 بعد گزینه 3 رو انتخاب میکنیم

```
1) Optimize for TCP / WebSocket (BBR + large TCP buffers)
2) Optimize for KCP / QUIC (UDP buffers)
3) Both + Extra high-BW tweaks
Select:

```


در انتها دو تا سرور رو ریبوت کنید و دوباره منو رو اجرا کنید.

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

از ما تعداد تانل های tcp رو میخواد

```
TCP count:
```

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


### روی سرور خارج


وارد منوی 10 شده و سپس گزینه 2 رو میزنیم

```
10. Aggregation Multi-Tunnel ba HAProxy (Bandwidth bala)
```


```
2) Kharej (frpc)  ← baad, line-haye compact az Iran ra paste kon

```

اسکریپت از ما آدرس آی پی سرور ایران رو میخواد


```
--- Configuring KHAREJ side (frpc clients) ---
IP ya domain server Iran (hamanja ke frps + HAProxy hast).
  Mesal: 2.3.4.5   ya   iran.example.com
Iran Server IP/Domain:
```

آی پی سرور ایران رو وارد میکنیم و Enter میزنیم


توی قسمت بعدی از ما میخواد پورت کانفیگ VPN رو وارد کنیم، روی سرور من برای 443 هست و عدد 443 رو وارد میکنم

```
Local service port(s) on THIS server (Kharej)
Inja Xray/service rooye 127.0.0.1 gush midahad (na port public Iran).
Agar chand config Xray dari, baraye har goruh tunnel localPort joda bedeh.
  Mesal 1: 443                    → hame tunnel-ha be 443
  Mesal 2: 1=443,2=443,3=2080,4=2080
  Mesal 3: 1-2=443,3-4=2090,5-6=8080
  Mesal 4: 443,8080               → avalin port = default (443)
Default: 443
In adad bayad ba inbound Xray rooye HAMIN server yeki bashad.
  Agar HAProxy Iran port 443 → tunnel 1-2 va Xray Kharej :443  →  1-2=443
  Agar HAProxy Iran port 2090 → tunnel 3-4 va Xray :2090 →  3-4=2090
  Port public Iran ra inja NA-nevis; faqat port local Xray/service.
Local port map [443]:
```

در مرحله بعدی از وارد کردن کانفیگ ها رو میخواد

باید لینک هایی که توی سرور ایران برامون نمایش داده شده رو اینجا وارد کنیم


توی سرور ایران این لینک ها به من داده شد
```
4,tcp,57909,nZdawJt9GmnFUTaq,20400,21400
5,tcp,46175,rZdJtnGMYnFUymoi,20401,21401
6,tcp,42109,jZdJt9GMYghfgTai,20402,21402
7,ws,41076,oZdJt9GMYndyasdf,20403,21403
8,ws,46759,qZdJt9GMdYnszcvai,20404,21404
9,ws,46192,sZdJt9GsMYnFupak,20405,21405
```
همینا رو paste میکنم و Enter میزنم

برای تایید اتمام لینک ها دوباره Enter میزنم



بعد از زدن Enter سرور شروع به ساختن کانفیگ ها و برقراری تانل میکنه


درانتها هم این متن رو نشون میده

```
================ KHAREJ SIDE READY ================
Primary local service port used: 443
Note: HAProxy on Iran routes different *public* ports to different tunnel groups.
On Kharej the real service usually listens on one port; all tunnels of a group
point to that same local service. Multiple public ports → same backend is fine.

Test: iperf3 from Iran to the aggregated iperf port with -P 16
===================================================

Press Enter to return...
```

---------

### چک کردن وضعیت برقراری اتصال تانل ها

برای چک کردن سلامت تانل ها همیشه باید از سرور خارج چک کنیم

از منوی شماره 4 وارد شده

```
4. Check Salamat Tunnel
```


بعد نوع پروتوکل رو میپرسه

```
Select Protocol:
  1) TCP          (Best pure performance / recommended for aggregation)
  2) KCP          (Good for lossy networks)
  3) QUIC         (Modern + good bandwidth)
  4) WebSocket    (Bypass firewall/proxy)
Choose [1-4]:
```

توی منوی بالا نشون میده نوع تانل ها چیه؟


<img width="781" height="508" alt="image" src="https://github.com/user-attachments/assets/5239aacc-f7f7-40bd-92d1-753f136d6f3c" />


مثلا من میخوام وضعیت تانل شماره 3 رو چک کنم





مشخصات تانل من اینه

```
Tunnel 3 [TCP Client / KHAREJ | Name: agg3] Status: [ONLINE] | Ports: [20102,21102]
```

چون tcp هست گزینه 1 رو انتخاب میکنم

بعد ازم شماره تانل رو میپرسه 
```
Enter Tunnel Index (1 to 10):

```

شماره تانل من شماره 3 هست، عدد 3 رو وارد میکنم، در انتها وضعیت تانل رو نشون میده که وصل هست یا نه؟



<img width="767" height="604" alt="image" src="https://github.com/user-attachments/assets/76740903-3ff2-4689-b728-3f64f2d9c94e" />







