# -*- coding: utf-8 -*-
"""
WeiboDeepAnalyzer FastAPI 后端实现示例
方案二：异步任务 + 轮询

使用方法：
1. 安装依赖: pip install fastapi uvicorn
2. 运行服务: uvicorn api_server:app --host 0.0.0.0 --port 8000
3. 访问文档: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import asyncio
from datetime import datetime
import traceback

from WeiboDeepAnalyzer import WeiboDeepAnalyzer

app = FastAPI(
    title="微博深度分析API",
    description="单条微博深度分析工具 - 支持内容、评论、转发完整分析",
    version="1.0.0"
)

# 允许跨域（前端访问需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 任务存储（生产环境建议使用 Redis）
tasks: Dict[str, Dict[str, Any]] = {}


# ==================== 请求模型 ====================

class AnalyzeRequest(BaseModel):
    """分析请求模型"""
    wid: str  # 微博ID
    max_comment_pages: Optional[int] = None  # 评论最大页数
    max_repost_pages: Optional[int] = None    # 转发最大页数
    download_images: bool = False             # 是否下载图片
    cookie: Optional[str] = None              # 自定义Cookie（可选）


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str
    status: str  # pending, running, completed, failed, cancelled
    progress: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
    request_info: Optional[Dict[str, Any]] = None  # 任务请求信息


# ==================== 辅助函数 ====================

def _create_task(task_id: str, request_info: Optional[Dict] = None) -> Dict[str, Any]:
    """创建新任务"""
    task = {
        'task_id': task_id,
        'status': 'pending',
        'progress': None,
        'result': None,
        'error': None,
        'request_info': request_info,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    tasks[task_id] = task
    return task


def _update_task_status(task_id: str, status: str, progress: Optional[Dict] = None, 
                       result: Optional[Dict] = None, error: Optional[str] = None):
    """更新任务状态"""
    if task_id in tasks:
        tasks[task_id]['status'] = status
        tasks[task_id]['updated_at'] = datetime.now().isoformat()
        if progress is not None:
            tasks[task_id]['progress'] = progress
        if result is not None:
            tasks[task_id]['result'] = result
        if error is not None:
            tasks[task_id]['error'] = error


def _run_analysis_sync(task_id: str, request: AnalyzeRequest):
    """
    同步执行分析任务（在后台线程中运行）
    
    注意：WeiboDeepAnalyzer 是同步的，需要在后台线程中执行
    以避免阻塞 FastAPI 的事件循环
    """
    try:
        _update_task_status(task_id, 'running', progress={
            'step': '初始化分析器',
            'current': 0,
            'total': 4,
            'message': '正在初始化分析器...'
        })
        
        # 创建分析器
        analyzer = WeiboDeepAnalyzer(
            wid=request.wid,
            cookie=request.cookie,
            download_images=request.download_images
        )
        
        # 1. 提取微博内容
        _update_task_status(task_id, 'running', progress={
            'step': '正在提取微博内容',
            'current': 1,
            'total': 4,
            'message': '正在提取微博完整内容...'
        })
        if not analyzer.get_weibo_content():
            raise Exception('无法获取微博内容，请检查 Cookie 是否有效或微博ID是否正确')
        
        # 2. 爬取评论
        _update_task_status(task_id, 'running', progress={
            'step': '正在爬取评论',
            'current': 2,
            'total': 4,
            'message': f'正在爬取评论（最大页数: {request.max_comment_pages or "无限制"}）...'
        })
        analyzer.get_all_comments(max_pages=request.max_comment_pages)
        
        # 3. 爬取转发
        _update_task_status(task_id, 'running', progress={
            'step': '正在爬取转发',
            'current': 3,
            'total': 4,
            'message': f'正在爬取转发（最大页数: {request.max_repost_pages or "无限制"}）...'
        })
        analyzer.get_all_reposts(max_pages=request.max_repost_pages)
        
        # 4. 生成统计
        _update_task_status(task_id, 'running', progress={
            'step': '正在生成统计分析',
            'current': 4,
            'total': 4,
            'message': '正在生成统计分析...'
        })
        analyzer.generate_stats()
        
        # 组装结果（复用 export_json 的数据结构）
        result = {
            'weibo_content': analyzer.weibo_data,
            'comments': analyzer.comments_data,
            'reposts': analyzer.reposts_data,
            'stats': analyzer.stats,
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # 可选：保存 CSV 文件（如果需要）
        # analyzer.export_csv()
        
        _update_task_status(task_id, 'completed', result=result, progress={
            'step': '分析完成',
            'current': 4,
            'total': 4,
            'message': f'分析完成！共获取 {len(analyzer.comments_data)} 条评论，{len(analyzer.reposts_data)} 条转发'
        })
        
    except Exception as e:
        error_msg = f'{str(e)}\n{traceback.format_exc()}'
        _update_task_status(task_id, 'failed', error=error_msg)


async def _run_analysis(task_id: str, request: AnalyzeRequest):
    """
    异步包装器，在后台线程中执行同步的分析任务
    """
    # 使用 run_in_executor 在线程池中执行同步函数
    # 这样不会阻塞 FastAPI 的事件循环
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_analysis_sync, task_id, request)


# ==================== API 路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "微博深度分析API",
        "version": "1.0.0",
        "docs": "/docs",
        "api": {
            "submit_task": "POST /api/analyze",
            "check_status": "GET /api/tasks/{task_id}",
            "get_result": "GET /api/tasks/{task_id}/result",
            "cancel_task": "DELETE /api/tasks/{task_id}",
            "list_tasks": "GET /api/tasks"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len([t for t in tasks.values() if t['status'] in ['pending', 'running']])
    }


@app.post("/api/analyze", response_model=TaskResponse)
async def create_analysis_task(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    提交分析任务（异步执行）
    
    返回任务ID，前端可以轮询查询进度和结果
    
    请求参数：
    - wid: 微博ID（必填）
    - max_comment_pages: 评论最大爬取页数（可选，None表示全部）
    - max_repost_pages: 转发最大爬取页数（可选，None表示全部）
    - download_images: 是否下载图片（默认False）
    - cookie: 自定义Cookie（可选，不传则使用环境变量或.env文件）
    """
    task_id = str(uuid.uuid4())
    
    # 保存请求信息
    request_info = {
        'wid': request.wid,
        'max_comment_pages': request.max_comment_pages,
        'max_repost_pages': request.max_repost_pages,
        'download_images': request.download_images
    }
    
    _create_task(task_id, request_info=request_info)
    
    # 在后台执行分析任务
    background_tasks.add_task(_run_analysis, task_id, request)
    
    return TaskResponse(
        task_id=task_id,
        status='pending',
        message='分析任务已提交，请使用 task_id 查询进度。建议每2-5秒轮询一次 /api/tasks/{task_id}'
    )


@app.get("/api/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态和进度
    
    前端可以定期轮询此接口获取进度
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    return TaskStatusResponse(**task)


@app.get("/api/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """
    获取任务结果（仅当任务完成时）
    
    如果任务还在进行中，返回进度信息
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    
    if task['status'] == 'completed':
        return {
            'status': 'completed',
            'result': task['result']
        }
    elif task['status'] == 'failed':
        return {
            'status': 'failed',
            'error': task['error']
        }
    else:
        return {
            'status': task['status'],
            'progress': task['progress'],
            'message': '任务仍在进行中，请稍后查询'
        }


@app.delete("/api/tasks/{task_id}")
async def cancel_task(task_id: str):
    """
    取消任务（如果任务还在运行）
    
    注意：当前实现中，已在执行的任务无法真正取消
    生产环境可以使用 Celery 等支持任务取消的框架
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    if task['status'] in ['completed', 'failed']:
        raise HTTPException(status_code=400, detail="任务已完成或已失败，无法取消")
    
    # 标记为取消（实际执行仍会继续）
    task['status'] = 'cancelled'
    task['updated_at'] = datetime.now().isoformat()
    
    return {"message": "任务已标记为取消"}


@app.get("/api/tasks")
async def list_tasks(limit: int = 20, status: Optional[str] = None):
    """
    列出所有任务（用于调试和管理）
    
    Args:
        limit: 返回任务数量限制（默认20）
        status: 筛选任务状态（可选：pending, running, completed, failed, cancelled）
    
    生产环境可能需要分页和权限控制
    """
    task_list = list(tasks.values())
    
    # 按创建时间倒序排序
    task_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    # 状态筛选
    if status:
        task_list = [t for t in task_list if t['status'] == status]
    
    # 统计各状态任务数
    status_counts = {}
    for task in tasks.values():
        status_counts[task['status']] = status_counts.get(task['status'], 0) + 1
    
    return {
        'total': len(tasks),
        'filtered': len(task_list),
        'status_counts': status_counts,
        'tasks': task_list[:limit]
    }


# ==================== 可选：同步API（方案一） ====================

@app.post("/api/analyze/sync")
async def analyze_sync(request: AnalyzeRequest):
    """
    同步分析接口（方案一）
    
    直接返回完整结果，适合数据量小的情况
    ⚠️ 警告：如果数据量大，可能超时
    """
    try:
        analyzer = WeiboDeepAnalyzer(
            wid=request.wid,
            cookie=request.cookie,
            download_images=request.download_images
        )
        
        # 执行完整分析
        success = analyzer.analyze(
            max_comment_pages=request.max_comment_pages,
            max_repost_pages=request.max_repost_pages
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="分析失败")
        
        # 返回结果
        result = {
            'weibo_content': analyzer.weibo_data,
            'comments': analyzer.comments_data,
            'reposts': analyzer.reposts_data,
            'stats': analyzer.stats,
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

