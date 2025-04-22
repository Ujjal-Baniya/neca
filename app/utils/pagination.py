"""Pagination utilities."""
from flask import request
from flask_sqlalchemy import Pagination

def create_paginated_list(items, page, per_page):
    """Create a paginated object from a list of items."""
    total = len(items)
    
    # Calculate start and end indices
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    
    # Get items for current page
    items_page = items[start:end]
    
    # Create pagination object
    return Pagination(query=None, page=page, per_page=per_page, 
                      total=total, items=items_page)

def get_pagination_args():
    """Extract pagination arguments from request."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Ensure reasonable values
    page = max(1, page)
    per_page = min(max(1, per_page), 100)  # Max 100 items per page
    
    return page, per_page