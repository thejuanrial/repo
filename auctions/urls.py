from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("category/", views.categories, name="categories"),
    path("category/<str:category>/", views.category, name="category"),
    path("create_listing/", views.create_listing, name="create_listing"),
    path("your_listings/", views.your_listings, name="your_listings"),
    path("won_listings/", views.won_listings, name="won_listings"),
    path("watch_list/", views.watch_list, name="watch_list"),
    path("listing/<int:listing_id>/", views.view_listing, name="listing"),
    path("listing/<int:listing_id>/watch/", views.watch, name="watch"),
    path("listing/<int:listing_id>/close/", views.close_auction, name="close_auction"),
    path("listing/<int:listing_id>/bid/", views.bid, name="bid"),
    path("listing/<int:listing_id>/comment/", views.comment, name="comment"),
    path('otp-verification/', views.otp_verification, name='otp_verification'),
    path('otp-success/', views.otp_success, name='otp_success'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-password-otp/', views.password_otp, name='password_otp'),
    path('reset-password/', views.password_reset_success, name='password_reset_success'),
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/edit/password/', views.edit_password, name='edit_password'),
    path('forbidden/', views.forbidden_view, name='forbidden'),

    # ---- Admin Dashboard ----
    path('admin-dashboard/', views.admin_view, name='admin_view'),
    path("admin-dashboard/manage-users", views.manage_users, name="manage_users"),
    path("admin-dashboard/manage-listings", views.manage_listings, name="manage_listings"),
    path("admin-dashboard/reports", views.reports, name="reports"),

    # Listing actions (admin)
    path('deactivate_listing/<int:listing_id>/', views.deactivate_listing, name='deactivate_listing'),
    path('delete_listing/<int:listing_id>/', views.delete_listing, name='delete_listing'),
    path('admin-dashboard/create-listing/', views.admin_create_listing, name='admin_create_listing'),
    path('admin-dashboard/edit-listing/<int:listing_id>/', views.admin_edit_listing, name='admin_edit_listing'),
    path('admin-dashboard/reactivate-listing/<int:listing_id>/', views.reactivate_listing, name='reactivate_listing'),

    # Category management (admin)
    path('admin-dashboard/manage-categories/', views.manage_categories, name='manage_categories'),
    path('admin-dashboard/edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('admin-dashboard/delete-category/<int:category_id>/', views.delete_category, name='delete_category'),

    # User management (admin)
    path('admin-dashboard/create-user/', views.admin_create_user, name='admin_create_user'),
    path('admin-dashboard/edit-user/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('admin-dashboard/delete-user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-dashboard/toggle-user/<int:user_id>/', views.admin_toggle_user, name='admin_toggle_user'),

    # Comments management (admin)
    path('admin-dashboard/manage-comments/', views.manage_comments, name='manage_comments'),
    path('admin-dashboard/delete-comment/<int:comment_id>/', views.admin_delete_comment, name='admin_delete_comment'),

    # Bids management (admin)
    path('admin-dashboard/manage-bids/', views.manage_bids, name='manage_bids'),
    path('admin-dashboard/delete-bid/<int:bid_id>/', views.admin_delete_bid, name='admin_delete_bid'),

    # Site configuration (admin)
    path('admin-dashboard/site-config/', views.admin_site_config, name='admin_site_config'),
    path('admin-dashboard/customize-home/', views.admin_customize_home, name='admin_customize_home'),
]
