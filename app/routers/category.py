from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, Session
from app.models import Category, Todo, TodoCategory, CategoryResponse, TodoResponse, RegularUser
from app.auth import AuthDep, SessionDep

category_router = APIRouter(tags=["Category"])

@category_router.post("/category", response_model=CategoryResponse)
def create_category(text: str, db: SessionDep, user: AuthDep):
    new_cat = Category(user_id=user.id, text=text)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return CategoryResponse(id=new_cat.id, text=new_cat.text)

@category_router.post("/todo/{todo_id}/category/{cat_id}", response_model=TodoResponse)
def add_category_to_todo(todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):
    todo = db.get(Todo, todo_id)
    if not todo or todo.user_id != user.id:
        raise HTTPException(status_code=404, detail="Todo not found or not authorized")

    category = db.get(Category, cat_id)
    if not category or category.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found or not authorized")

    if category not in todo.categories:
        todo.categories.append(category)
        db.add(todo)
        db.commit()
        db.refresh(todo)
    
    return TodoResponse(
        id=todo.id,
        text=todo.text,
        done=todo.done,
        categories=todo.get_category_response()
    )

@category_router.delete("/todo/{todo_id}/category/{cat_id}", response_model=TodoResponse)
def remove_category_from_todo(todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):
    todo = db.get(Todo, todo_id)
    if not todo or todo.user_id != user.id:
        raise HTTPException(status_code=404, detail="Todo not found or not authorized")

    category = db.get(Category, cat_id)
    if not category or category not in todo.categories:
        raise HTTPException(status_code=404, detail="Category not assigned to this todo")

    todo.categories.remove(category)
    db.add(todo)
    db.commit()
    db.refresh(todo)

    return TodoResponse(
        id=todo.id,
        text=todo.text,
        done=todo.done,
        categories=todo.get_category_response()
    )

@category_router.get("/category/{cat_id}/todos", response_model=list[TodoResponse])
def get_todos_for_category(cat_id: int, db: SessionDep, user: AuthDep):
    category = db.get(Category, cat_id)
    if not category or category.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found or not authorized")

    todos = []
    for todo in category.todos:
        todos.append(TodoResponse(
            id=todo.id,
            text=todo.text,
            done=todo.done,
            categories=todo.get_category_response()
        ))
    return todos