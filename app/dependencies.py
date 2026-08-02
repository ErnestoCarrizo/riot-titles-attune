from fastapi import Request


def get_catalog_service(request: Request):
    return request.app.state.catalog_service


def get_progress_service(request: Request):
    return request.app.state.progress_service
