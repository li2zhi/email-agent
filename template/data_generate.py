import json
import os
from typing import List, Dict
import random

class TestDataManager:
    def __init__(self, filename: str = "test_emails.json"):
        self.filename = filename

    def save_test_data(self, data: List[Dict]) -> bool:
        """
        将测试数据保存到JSON文件
        """
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"测试数据已保存到 {self.filename}")
            return True
        except Exception as e:
            print(f"保存文件时出错: {e}")
            return False

    def load_test_data(self) -> List[Dict]:
        """
        从JSON文件加载测试数据
        """
        try:
            if not os.path.exists(self.filename):
                print(f"文件 {self.filename} 不存在")
                return []

            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"从 {self.filename} 加载了 {len(data)} 条测试数据")
            random.shuffle(data)
            return data
        except Exception as e:
            print(f"加载文件时出错: {e}")
            return []

    def add_test_data(self, new_data: Dict) -> bool:
        """
        向现有测试数据中添加新条目
        """
        try:
            existing_data = self.load_test_data()
            existing_data.append(new_data)
            return self.save_test_data(existing_data)
        except Exception as e:
            print(f"添加数据时出错: {e}")
            return False

    def display_test_data(self, data: List[Dict] = None):
        """
        显示测试数据的统计信息
        """
        if data is None:
            data = self.load_test_data()

        if not data:
            print("没有测试数据")
            return

        categories = {}
        for item in data:
            subject = item.get('subject', '')
            if '营销' in subject or '促销' in subject:
                categories.setdefault('营销邮件', 0)
                categories['营销邮件'] += 1
            elif '中奖' in subject or '安全' in subject:
                categories.setdefault('垃圾邮件', 0)
                categories['垃圾邮件'] += 1
            elif '请假' in subject or '休假' in subject:
                categories.setdefault('请假通知', 0)
                categories['请假通知'] += 1
            elif '部署' in subject or '系统' in subject:
                categories.setdefault('系统通知', 0)
                categories['系统通知'] += 1
            elif '疑问' in subject or '咨询' in subject:
                categories.setdefault('团队提问', 0)
                categories['团队提问'] += 1
            elif '会议' in subject or '邀请' in subject:
                categories.setdefault('会议邀请', 0)
                categories['会议邀请'] += 1
            else:
                categories.setdefault('其他', 0)
                categories['其他'] += 1

        print(f"\n测试数据统计 (总计: {len(data)} 条):")
        for category, count in categories.items():
            print(f"  {category}: {count} 条")