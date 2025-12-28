from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SplitRequestSerializer, SplitResponseSerializer, compute_split_response


class HealthzView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"ok": True})


class SplitBillView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        req = SplitRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        payload = compute_split_response(req.validated_data)
        resp = SplitResponseSerializer(data=payload)
        resp.is_valid(raise_exception=True)
        return Response(resp.data, status=status.HTTP_200_OK)
