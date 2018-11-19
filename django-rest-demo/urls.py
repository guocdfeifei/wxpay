url(r'^wxqrcode/$', views.WxpaySignView.as_view(), name='WxpaySignView')
url(r"^wxnotify/$", views.generate_qrcode1, name="wxnotify"),