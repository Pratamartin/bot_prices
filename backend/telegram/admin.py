from django.contrib import admin

from .models import SearchLog


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"user_id",
		"username",
		"query_clean",
		"best_store",
		"best_price",
		"created_at",
	)
	list_filter = ("best_store", "created_at")
	search_fields = ("username", "query_raw", "query_clean", "best_title", "best_store")
	readonly_fields = ("created_at",)
	ordering = ("-created_at",)
	list_per_page = 50
