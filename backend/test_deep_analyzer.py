# -*- coding: utf-8 -*-
"""
WeiboDeepAnalyzer 测试脚本
用于快速测试单条微博深度分析功能
"""

from WeiboDeepAnalyzer import WeiboDeepAnalyzer
import time

def test_basic_usage():
    """测试基本功能"""
    print("=" * 80)
    print("测试1: 基本用法 - 完整分析（限制页数）")
    print("=" * 80)
    
    # 使用一个已知的微博ID进行测试
    # 请替换为你想分析的微博ID
    wid = 'QbelLys5Z'  # 这是一个示例ID，请替换为实际的微博ID
    
    try:
        analyzer = WeiboDeepAnalyzer(wid=wid)
        
        # 限制评论和转发各爬取5页（用于快速测试）
        success = analyzer.analyze(max_comment_pages=5, max_repost_pages=5)
        
        if success:
            print("\n✓ 测试通过！")
            print(f"数据已保存到: {analyzer.wid_dir}")
        else:
            print("\n✗ 测试失败")
            
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()


def test_step_by_step():
    """测试分步执行"""
    print("\n" + "=" * 80)
    print("测试2: 分步执行 - 仅获取微博内容和少量评论")
    print("=" * 80)
    
    wid = 'QbelLys5Z'  # 请替换为实际的微博ID
    
    try:
        analyzer = WeiboDeepAnalyzer(wid=wid, output_dir='test_output')
        
        # 步骤1：只获取微博内容
        print("\n执行步骤1: 获取微博内容")
        weibo_data = analyzer.get_weibo_content()
        if weibo_data:
            print(f"✓ 微博内容: {weibo_data['content'][:100]}...")
        
        # 步骤2：只获取前2页评论
        print("\n执行步骤2: 获取评论（限2页）")
        comments = analyzer.get_all_comments(max_pages=2)
        print(f"✓ 获取到 {len(comments)} 条评论")
        
        # 步骤3：生成统计
        print("\n执行步骤3: 生成统计")
        stats = analyzer.generate_stats()
        print(f"✓ 统计完成")
        
        # 步骤4：导出JSON
        print("\n执行步骤4: 导出数据")
        analyzer.export_json()
        print(f"✓ 数据已导出")
        
        print("\n✓ 分步测试通过！")
        
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()


def test_data_access():
    """测试数据访问"""
    print("\n" + "=" * 80)
    print("测试3: 数据访问 - 查看爬取的数据结构")
    print("=" * 80)
    
    wid = 'QbelLys5Z'  # 请替换为实际的微博ID
    
    try:
        analyzer = WeiboDeepAnalyzer(wid=wid, output_dir='test_output')
        
        # 获取数据
        analyzer.get_weibo_content()
        analyzer.get_all_comments(max_pages=1)
        analyzer.get_all_reposts(max_pages=1)
        
        # 访问数据
        print("\n微博数据结构:")
        print(f"  - 作者: {analyzer.weibo_data.get('user_name')}")
        print(f"  - 内容长度: {len(analyzer.weibo_data.get('content', ''))}")
        print(f"  - 图片数量: {analyzer.weibo_data.get('image_count', 0)}")
        print(f"  - 点赞数: {analyzer.weibo_data.get('like_count', 0)}")
        
        print("\n评论数据:")
        if analyzer.comments_data:
            first_comment = analyzer.comments_data[0]
            print(f"  - 第一条评论者: {first_comment.get('commenter_name')}")
            print(f"  - 评论内容: {first_comment.get('content')[:50]}...")
            print(f"  - 总评论数: {len(analyzer.comments_data)}")
        else:
            print("  - 暂无评论数据")
        
        print("\n转发数据:")
        if analyzer.reposts_data:
            first_repost = analyzer.reposts_data[0]
            print(f"  - 第一个转发者: {first_repost.get('user_name')}")
            print(f"  - 转发内容: {first_repost.get('content')[:50] if first_repost.get('content') else '（无内容）'}...")
            print(f"  - 总转发数: {len(analyzer.reposts_data)}")
        else:
            print("  - 暂无转发数据")
        
        print("\n✓ 数据访问测试通过！")
        
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()


def interactive_test():
    """交互式测试"""
    print("\n" + "=" * 80)
    print("交互式测试")
    print("=" * 80)
    
    wid = input("\n请输入要分析的微博ID (wid): ").strip()
    
    if not wid:
        print("未输入微博ID，使用默认示例ID: QbelLys5Z")
        wid = 'QbelLys5Z'
    
    try:
        max_comment = input("评论最大爬取页数 (直接回车表示5页): ").strip()
        max_comment = int(max_comment) if max_comment else 5
        
        max_repost = input("转发最大爬取页数 (直接回车表示5页): ").strip()
        max_repost = int(max_repost) if max_repost else 5
        
        print(f"\n开始分析微博: {wid}")
        print(f"评论页数限制: {max_comment}")
        print(f"转发页数限制: {max_repost}")
        
        analyzer = WeiboDeepAnalyzer(wid=wid)
        success = analyzer.analyze(max_comment_pages=max_comment, max_repost_pages=max_repost)
        
        if success:
            print(f"\n✓ 分析完成！数据已保存到: {analyzer.wid_dir}")
        else:
            print("\n✗ 分析失败")
            
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print(f"\n✗ 出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    """
    运行测试
    
    使用方法：
    1. 确保已配置好Cookie（环境变量或.env文件）
    2. 运行此脚本: python test_deep_analyzer.py
    3. 选择要运行的测试
    """
    
    print("WeiboDeepAnalyzer 测试脚本")
    print("=" * 80)
    print("请选择测试模式:")
    print("1. 基本功能测试（完整分析，限制页数）")
    print("2. 分步执行测试（演示各个功能模块）")
    print("3. 数据访问测试（查看数据结构）")
    print("4. 交互式测试（自定义参数）")
    print("5. 运行所有测试")
    print("=" * 80)
    
    choice = input("\n请输入选项 (1-5, 直接回车默认为1): ").strip()
    
    if not choice or choice == '1':
        test_basic_usage()
    elif choice == '2':
        test_step_by_step()
    elif choice == '3':
        test_data_access()
    elif choice == '4':
        interactive_test()
    elif choice == '5':
        test_basic_usage()
        time.sleep(2)
        test_step_by_step()
        time.sleep(2)
        test_data_access()
    else:
        print("无效选项")
    
    print("\n测试完成！")

