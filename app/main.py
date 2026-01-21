from fastapi import FastAPI
from app.routers.user_router import router as users_router
from app.routers.post_router import router as posts_router
from app.routers.todo_router import router as todo_router
from app.routers.auth_router import router as auth_router

app = FastAPI()

app.include_router(users_router)
app.include_router(posts_router)
app.include_router(todo_router) 


app.include_router(auth_router)