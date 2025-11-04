# -*- coding: utf-8 -*-
"""
WeiboDeepAnalyzer 高级使用示例
展示更多实用场景和数据处理方法
"""

from WeiboDeepAnalyzer import WeiboDeepAnalyzer
import json
import time
import os


def example1_batch_analysis():
    """
    示例1：批量分析多条微博
    适用场景：分析多条相关微博，比如某个话题下的热门微博
    """
    print("=" * 80)
    print("示例1: 批量分析多条微博")
    print("=" * 80)
    
    # 要分析的微博ID列表
    wids = [
        'QbelLys5Z',  # 微博1
        # 'xxxxx',    # 微博2（添加更多ID）
        # 'xxxxx',    # 微博3
    ]
    
    results = []
    
    for i, wid in enumerate(wids, 1):
        print(f"\n正在分析第 {i}/{len(wids)} 条微博: {wid}")
        
        try:
            analyzer = WeiboDeepAnalyzer(wid=wid)
            success = analyzer.analyze(max_comment_pages=5, max_repost_pages=5)
            
            if success:
                results.append({
                    'wid': wid,
                    'status': 'success',
                    'stats': analyzer.stats
                })
            else:
                results.append({
                    'wid': wid,
                    'status': 'failed'
                })
            
            # 避免请求过快
            if i < len(wids):
                print("等待10秒后继续...")
                time.sleep(10)
                
        except Exception as e:
            print(f"分析失败: {e}")
            results.append({
                'wid': wid,
                'status': 'error',
                'error': str(e)
            })
    
    # 保存批量分析结果
    output_file = 'weibo_analysis/batch_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 批量分析完成！结果已保存到: {output_file}")


def example2_comment_analysis():
    """
    示例2：深度评论分析
    适用场景：分析评论内容，找出热门评论、活跃用户等
    """
    print("\n" + "=" * 80)
    print("示例2: 深度评论分析")
    print("=" * 80)
    
    wid = 'QbelLys5Z'  # 替换为你要分析的微博ID
    
    analyzer = WeiboDeepAnalyzer(wid=wid)
    analyzer.get_weibo_content()
    comments = analyzer.get_all_comments(max_pages=10)
    
    if not comments:
        print("没有评论数据")
        return
    
    # 分析1：找出最热门的评论（按点赞数排序）
    print("\n【最热门评论 Top 10】")
    sorted_comments = sorted(comments, key=lambda x: x['like_count'], reverse=True)
    for i, comment in enumerate(sorted_comments[:10], 1):
        print(f"{i}. {comment['commenter_name']} (赞:{comment['like_count']})")
        print(f"   {comment['content'][:100]}...")
    
    # 分析2：找出最活跃的评论者
    print("\n【最活跃评论者 Top 10】")
    from collections import Counter
    commenter_counts = Counter([c['commenter_name'] for c in comments])
    for i, (name, count) in enumerate(commenter_counts.most_common(10), 1):
        print(f"{i}. {name}: {count} 条评论")
    
    # 分析3：评论时间分布
    print("\n【评论时间分布】")
    time_stats = {}
    for comment in comments:
        pub_time = comment['publish_time']
        if pub_time:
            # 提取小时
            try:
                hour = pub_time.split(' ')[1].split(':')[0] if ' ' in pub_time else '未知'
                time_stats[hour] = time_stats.get(hour, 0) + 1
            except:
                pass
    
    for hour in sorted(time_stats.keys()):
        bar = '█' * (time_stats[hour] // 5 + 1)
        print(f"{hour}时: {bar} ({time_stats[hour]}条)")
    
    # 分析4：评论长度分布
    print("\n【评论长度统计】")
    lengths = [len(c['content']) for c in comments if c['content']]
    if lengths:
        avg_length = sum(lengths) / len(lengths)
        max_length = max(lengths)
        min_length = min(lengths)
        print(f"平均长度: {avg_length:.1f} 字")
        print(f"最长评论: {max_length} 字")
        print(f"最短评论: {min_length} 字")
    
    # 保存分析结果
    analyzer.export_json()
    print(f"\n✓ 评论分析完成！")


def example3_repost_network():
    """
    示例3：转发网络分析
    适用场景：分析微博传播路径，找出关键传播节点
    """
    print("\n" + "=" * 80)
    print("示例3: 转发网络分析")
    print("=" * 80)
    
    wid = 'QbelLys5Z'  # 替换为你要分析的微博ID
    
    analyzer = WeiboDeepAnalyzer(wid=wid)
    analyzer.get_weibo_content()
    reposts = analyzer.get_all_reposts(max_pages=10)
    
    if not reposts:
        print("没有转发数据")
        return
    
    # 分析1：转发量最高的用户
    print("\n【转发影响力 Top 10】")
    sorted_reposts = sorted(reposts, key=lambda x: x['like_count'], reverse=True)
    for i, repost in enumerate(sorted_reposts[:10], 1):
        print(f"{i}. {repost['user_name']} (转发获赞:{repost['like_count']})")
        if repost['content']:
            print(f"   {repost['content'][:80]}...")
    
    # 分析2：转发内容类型分析
    print("\n【转发内容分析】")
    with_comment = sum(1 for r in reposts if r['content'] and len(r['content']) > 5)
    without_comment = len(reposts) - with_comment
    print(f"带评论转发: {with_comment} ({with_comment/len(reposts)*100:.1f}%)")
    print(f"纯转发: {without_comment} ({without_comment/len(reposts)*100:.1f}%)")
    
    # 分析3：转发时间分析
    print("\n【转发时间分布】")
    time_stats = {}
    for repost in reposts:
        pub_time = repost['publish_time']
        if pub_time:
            try:
                hour = pub_time.split(' ')[1].split(':')[0] if ' ' in pub_time else '未知'
                time_stats[hour] = time_stats.get(hour, 0) + 1
            except:
                pass
    
    for hour in sorted(time_stats.keys()):
        bar = '█' * (time_stats[hour] // 3 + 1)
        print(f"{hour}时: {bar} ({time_stats[hour]}次)")
    
    print(f"\n✓ 转发网络分析完成！")


def example4_data_export():
    """
    示例4：自定义数据导出
    适用场景：需要特定格式的数据，或者进行二次处理
    """
    print("\n" + "=" * 80)
    print("示例4: 自定义数据导出")
    print("=" * 80)
    
    wid = 'QbelLys5Z'  # 替换为你要分析的微博ID
    
    analyzer = WeiboDeepAnalyzer(wid=wid)
    analyzer.get_weibo_content()
    analyzer.get_all_comments(max_pages=5)
    analyzer.get_all_reposts(max_pages=5)
    analyzer.generate_stats()
    
    # 导出1：只导出高赞评论
    popular_comments = [
        c for c in analyzer.comments_data 
        if c['like_count'] >= 10
    ]
    
    output_file = os.path.join(analyzer.wid_dir, f'{wid}_popular_comments.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(popular_comments, f, ensure_ascii=False, indent=2)
    print(f"✓ 高赞评论已导出: {output_file}")
    
    # 导出2：只导出评论者信息（去重）
    unique_commenters = {}
    for c in analyzer.comments_data:
        uid = c['commenter_id']
        if uid and uid not in unique_commenters:
            unique_commenters[uid] = {
                'id': c['commenter_id'],
                'name': c['commenter_name'],
                'comment_count': 1
            }
        elif uid:
            unique_commenters[uid]['comment_count'] += 1
    
    output_file = os.path.join(analyzer.wid_dir, f'{wid}_commenters.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(list(unique_commenters.values()), f, ensure_ascii=False, indent=2)
    print(f"✓ 评论者信息已导出: {output_file}")
    
    # 导出3：生成简报
    report = f"""
# 微博 {wid} 分析简报

## 基本信息
- 作者: {analyzer.weibo_data['user_name']}
- 发布时间: {analyzer.weibo_data['publish_time']}
- 内容: {analyzer.weibo_data['content'][:100]}...

## 互动数据
- 点赞数: {analyzer.stats['interaction_stats']['like_count']}
- 转发数: {analyzer.stats['interaction_stats']['repost_count']}
- 评论数: {analyzer.stats['interaction_stats']['comment_count']}
- 总互动: {analyzer.stats['interaction_stats']['total_interactions']}

## Top评论者
"""
    for i, c in enumerate(analyzer.stats['comment_stats']['top_commenters'][:5], 1):
        report += f"{i}. {c['name']} - {c['count']}条评论\n"
    
    output_file = os.path.join(analyzer.wid_dir, f'{wid}_report.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ 分析简报已导出: {output_file}")
    
    print(f"\n✓ 自定义导出完成！")


def example5_incremental_crawl():
    """
    示例5：增量爬取（续爬）
    适用场景：之前爬取过，现在想补充新增的评论/转发
    """
    print("\n" + "=" * 80)
    print("示例5: 增量爬取示例")
    print("=" * 80)
    
    wid = 'QbelLys5Z'  # 替换为你要分析的微博ID
    
    # 检查是否已有数据
    json_file = f'weibo_analysis/{wid}/{wid}_complete.json'
    
    if os.path.exists(json_file):
        print(f"检测到已有数据: {json_file}")
        
        # 读取旧数据
        with open(json_file, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        
        old_comment_count = len(old_data.get('comments', []))
        old_repost_count = len(old_data.get('reposts', []))
        
        print(f"旧数据: {old_comment_count} 条评论, {old_repost_count} 条转发")
        
        # 重新爬取
        print("\n开始增量爬取...")
        analyzer = WeiboDeepAnalyzer(wid=wid)
        analyzer.analyze(max_comment_pages=20, max_repost_pages=20)
        
        new_comment_count = len(analyzer.comments_data)
        new_repost_count = len(analyzer.reposts_data)
        
        print(f"\n新数据: {new_comment_count} 条评论, {new_repost_count} 条转发")
        print(f"增量: +{new_comment_count - old_comment_count} 条评论, +{new_repost_count - old_repost_count} 条转发")
        
    else:
        print("未找到旧数据，执行首次爬取...")
        analyzer = WeiboDeepAnalyzer(wid=wid)
        analyzer.analyze(max_comment_pages=20, max_repost_pages=20)
    
    print(f"\n✓ 增量爬取完成！")


def example6_compare_weibos():
    """
    示例6：对比多条微博
    适用场景：对比不同微博的传播效果
    """
    print("\n" + "=" * 80)
    print("示例6: 对比多条微博")
    print("=" * 80)
    
    wids = ['wid1', 'wid2']  # 替换为要对比的微博ID
    
    comparison = []
    
    for wid in wids:
        try:
            analyzer = WeiboDeepAnalyzer(wid=wid)
            analyzer.get_weibo_content()
            analyzer.get_all_comments(max_pages=5)
            analyzer.get_all_reposts(max_pages=5)
            analyzer.generate_stats()
            
            comparison.append({
                'wid': wid,
                'author': analyzer.weibo_data['user_name'],
                'content_length': len(analyzer.weibo_data['content']),
                'like_count': analyzer.weibo_data['like_count'],
                'repost_count': len(analyzer.reposts_data),
                'comment_count': len(analyzer.comments_data),
                'total_interactions': analyzer.stats['interaction_stats']['total_interactions'],
            })
            
            time.sleep(5)
            
        except Exception as e:
            print(f"分析 {wid} 失败: {e}")
    
    # 打印对比结果
    print("\n【微博对比结果】")
    print(f"{'微博ID':<15} {'作者':<15} {'点赞':<8} {'转发':<8} {'评论':<8} {'总互动':<10}")
    print("-" * 80)
    for w in comparison:
        print(f"{w['wid']:<15} {w['author']:<15} {w['like_count']:<8} {w['repost_count']:<8} {w['comment_count']:<8} {w['total_interactions']:<10}")
    
    print(f"\n✓ 对比分析完成！")


if __name__ == '__main__':
    """
    运行高级示例
    
    使用方法：
    1. 根据需求修改每个示例函数中的微博ID
    2. 取消注释你想运行的示例
    3. 运行脚本
    """
    
    print("WeiboDeepAnalyzer 高级使用示例")
    print("=" * 80)
    print("可用示例：")
    print("1. 批量分析多条微博")
    print("2. 深度评论分析")
    print("3. 转发网络分析")
    print("4. 自定义数据导出")
    print("5. 增量爬取（续爬）")
    print("6. 对比多条微博")
    print("=" * 80)
    
    # 选择要运行的示例
    choice = input("\n请输入示例编号 (1-6): ").strip()
    
    try:
        if choice == '1':
            example1_batch_analysis()
        elif choice == '2':
            example2_comment_analysis()
        elif choice == '3':
            example3_repost_network()
        elif choice == '4':
            example4_data_export()
        elif choice == '5':
            example5_incremental_crawl()
        elif choice == '6':
            example6_compare_weibos()
        else:
            print("无效选项，运行示例2（深度评论分析）...")
            example2_comment_analysis()
            
    except Exception as e:
        print(f"\n❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n示例运行完成！")

