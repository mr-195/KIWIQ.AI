# backend/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GraphViewSet, RunConfigViewSet, NodeViewSet, EdgeViewSet
""" EdgeViewSet """

# Initialize router
router = DefaultRouter()
router.register(r'graphs', GraphViewSet, basename='graph')       # Graph endpoints
router.register(r'runs', RunConfigViewSet, basename='runconfig') # Run config endpoints
router.register(r'nodes', NodeViewSet, basename='node')          # Node endpoints
router.register(r'edges', EdgeViewSet, basename='edge')          # Edge endpoints

# Define URL patterns with only the router included
urlpatterns = router.urls
