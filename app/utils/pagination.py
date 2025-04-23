# Replace app/utils/pagination.py with:
"""Pagination utilities."""
from flask import request

class CustomPagination:
    """Custom pagination class that mimics Flask-SQLAlchemy's Pagination."""
    
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        
    @property
    def pages(self):
        """Calculate total number of pages."""
        if self.per_page == 0 or self.total == 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page
        
    @property
    def has_prev(self):
        """Check if there is a previous page."""
        return self.page > 1
        
    @property
    def has_next(self):
        """Check if there is a next page."""
        return self.page < self.pages
        
    @property
    def prev_num(self):
        """Get previous page number."""
        if not self.has_prev:
            return None
        return self.page - 1
        
    @property
    def next_num(self):
        """Get next page number."""
        if not self.has_next:
            return None
        return self.page + 1
        
    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        """Iterate through page numbers to display."""
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

def create_paginated_list(items, page, per_page):
    """Create a paginated object from a list of items."""
    total = len(items)
    
    # Calculate start and end indices
    start = (page - 1) * per_page
    end = min(start + per_page, total)
    
    # Get items for current page
    items_page = items[start:end]
    
    # Create pagination object
    return CustomPagination(items=items_page, page=page, per_page=per_page, total=total)

def get_pagination_args():
    """Extract pagination arguments from request."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Ensure reasonable values
    page = max(1, page)
    per_page = min(max(1, per_page), 100)  # Max 100 items per page
    
    return page, per_page