#二维码生成部分
class WxpaySignView(GenericAPIView):
    serializer_class = OrderSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        instance = Order.objects.create(**request.data)
        instance.out_trade_no = timezone.now().strftime('%Y%m%d') + '{}'.format(instance.id)
        instance.save()
        subject = serializer.validated_data.get('subject')
        total_amount = serializer.validated_data.get('total_amount')

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        notify_url = NOTIFY_URL
        product = {
            'attach': subject,
            'body': subject,
            'out_trade_no': instance.out_trade_no,
            'total_fee': total_amount,
        }
        img = qr_wxpay.generate_product_qr(product)
        img_io = StringIO()
        img.save(instance.out_trade_no+'.png')  # 直接将生成的QR放在了内存里, 请根据实际需求选择放在内存还是放在硬盘上
        encodestr=None
        with open(instance.out_trade_no+'.png', 'rb') as f:  # 以二进制读取图片
            data = f.read()
            encodestr = base64.b64encode(data)  # 得到 byte 编码的数据
        import os
        os.remove(instance.out_trade_no+'.png')
        return Response({'sign':instance.out_trade_no+'.png', 'out_trade_no': instance.out_trade_no,'base64_data':str(encodestr, 'utf-8')})

##反馈部分
def generate_qrcode1(request):
    # logger.warning("the get method request:", request,request.FILES,request.GET,request.POST,request.body)
    xml_str = str(request.body, encoding = "utf-8").replace('\r','').replace('\n','').replace('\t','')
    # logger.warning("the xml_str request:", xml_str, len(xml_str),type(xml_str))
    # out_trade_no = request.data.get('out_trade_no')
    # trade_no = request.data.get('transaction_id')
    # order1 = Order.objects.filter(out_trade_no='20181117173').first()
    # order1.content = xml_str
    # order1.save()
    ret, ret_dict = qr_wxpay.verify_notify(xml_str)
    # print(ret_dict['cash_fee'],'ret',ret,'ret_dict',ret_dict)
    begin_dict = ret_dict
    # 在这里添加订单更新逻辑
    if ret:
        ret_dict = {
            'return_code': 'SUCCESS',
            'return_msg': 'OK',
        }
        ret_xml = qr_wxpay.generate_notify_resp(ret_dict)
        # print('ret_dict',ret_dict)
        # print(ret_dict['cash_fee'],'ret',ret,'ret_dict',ret_dict)
        total_amount = int(begin_dict['cash_fee'])
        out_trade_no = begin_dict['out_trade_no']
        trade_no = begin_dict['transaction_id']
        order = Order.objects.filter(out_trade_no=out_trade_no).first()

        if order and order.status == 1:
            ret_xml = qr_wxpay.generate_notify_resp(ret_dict)
            # return ret_xml
            response = HttpResponse(ret_xml)
            return response
            # return Response(ret_xml)

        if order and order.status == 0:
            if "%s" % order.total_amount == "%s" % str(total_amount/100):
                order.trade_no = trade_no
                order.status = True
                order.content = order.content
                order.save()
    else:
        ret_dict = {
            'return_code': 'FAIL',
            'return_msg': 'verify error',
        }
        ret_xml = qr_wxpay.generate_notify_resp(ret_dict)
    # return ret_xml
    response = HttpResponse(ret_xml)
    return response