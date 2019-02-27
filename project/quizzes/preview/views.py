from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import PreviewSourceSerializer, PreviewResultSerializer
from .structs import PreviewResult

from common.katex import tex2html


class RenderPreviewAPIView(APIView):
    def post(self, request):
        src_serializer = PreviewSourceSerializer(data=request.data, many=True)
        src_serializer.is_valid(raise_exception=True)

        srcs = src_serializer.save()
        dsts = [PreviewResult(tex2html(block.tex)) for block in srcs]

        dst_serializer = PreviewResultSerializer(dsts, many=True)
        return Response(dst_serializer.data)
