# Tunnel-Protocol-tester

### FRP

```
bash frp_test.sh --iran-host IP.IP.IP.IP --iran-port 22 --iran-user root --iran-pass 'PASSWORD'
```

##### Example:

ار سرور خارج دستور رو اجرا میکنید

خودش به سرور ایران وصل میشه
فایل های مورد نیاز رو روی دو تا سرور نصب و تونل ها با پروتوکل ها رو راه اندازی و تست میگیره، در انتهای بهتون میگه که کدوم تانل ها اامکان برقراری داره

روی frp از پروتوکل های زیر تست میگیره


```
TCP
KCP
QUIC
WEB SOCKET
```

نمونه دستور اجرای برای سرور ابران با آی پی 2.3.4.5 با یوزر روت و پسورد دسترسی `qI78jNJGBSNB`

```
bash frp_test.sh --iran-host 2.3.4.5.6 --iran-port 22 --iran-user root --iran-pass 'qI78jNJGBSNB'
```
