import logging
import time
from typing import Dict, Any, List

try:
    from falkordb import FalkorDB
    FALKOR_AVAILABLE = True
except ImportError:
    FALKOR_AVAILABLE = False

class FalkorDBManager:
    """
    FalkorDB 연결을 관리하고 에피소드 그래프(Episode Graph) 작업을 처리합니다.
    스키마:
    (:Episode {id, timestamp, result})
    (:Action {type, target})
    (:Emotion {focus, effort, ...})
    
    (Episode)-[:EXECUTED]->(Action)
    (Episode)-[:STARTED_WITH]->(Emotion)
    (Episode)-[:ENDED_WITH]->(Emotion)
    """
    def __init__(self, host='localhost', port=6379):
        self.client = None
        self.graph = None
        self.host = host
        self.port = port
        self.connected = False
        
        if not FALKOR_AVAILABLE:
            logging.warning("[Memory] FalkorDB library not installed. Memory will be disabled.")

    def connect(self):
        if not FALKOR_AVAILABLE: return
        try:
            self.client = FalkorDB(host=self.host, port=self.port)
            # Create or Connect to Graph 'MACH_VII_MEMORY'
            self.graph = self.client.select_graph('MACH_VII_MEMORY')
            self.connected = True
            logging.info(f"[Memory] Connected to FalkorDB at {self.host}:{self.port}")
        except Exception as e:
            logging.error(f"[Memory] Connection Failed: {e}")
            self.connected = False

    def save_episode(self, episode_data: Dict[str, Any]):
        """
        완료된 에피소드를 그래프에 저장합니다.
        episode_data: {
            "id": str,
            "timestamp": float,
            "result": str, # success/failure
            "action": {"type": str, "target": str},
            "start_emotion": dict,
            "end_emotion": dict
        }
        """
        if not self.connected: 
            return

        try:
            # Cypher 쿼리를 사용하여 노드와 관계 생성
            query = """
            MERGE (e:Episode {id: $id, timestamp: $ts, result: $res})
            MERGE (a:Action {type: $act_type, target: $act_target})
            MERGE (e)-[:EXECUTED]->(a)
            
            CREATE (start_em:Emotion {focus: $s_focus, effort: $s_effort, frustration: $s_frust})
            CREATE (end_em:Emotion {focus: $e_focus, effort: $e_effort, frustration: $e_frust})
            
            MERGE (e)-[:STARTED_WITH]->(start_em)
            MERGE (e)-[:ENDED_WITH]->(end_em)
            """
            
            params = {
                'id': episode_data['id'],
                'ts': episode_data['timestamp'],
                'res': episode_data['result'],
                'act_type': episode_data['action'].get('type', 'unknown'),
                'act_target': str(episode_data['action'].get('target', 'none')),
                # 시작 감정
                's_focus': episode_data['start_emotion'].get('focus', 0.5),
                's_effort': episode_data['start_emotion'].get('effort', 0.0),
                's_frust': episode_data['start_emotion'].get('frustration', 0.0),
                # 종료 감정
                'e_focus': episode_data['end_emotion'].get('focus', 0.5),
                'e_effort': episode_data['end_emotion'].get('effort', 0.0),
                'e_frust': episode_data['end_emotion'].get('frustration', 0.0),
            }
            
            self.graph.query(query, params)
            logging.info(f"[Memory] Episode {episode_data['id']} saved.")
            
        except Exception as e:
            logging.error(f"[Memory] Save Error: {e}")

    def get_recent_success_rate(self, action_type: str = None, target: str = None) -> float:
        """
        특정 행동 유형 및 타겟의 성공률을 조회합니다.
        둘 다 None이면 0.5를 반환합니다.
        """
        if not self.connected: return 0.5
        
        try:
            # 동적으로 쿼리를 구성하거나 선택적 매칭 사용
            # 간단한 방식: 제공된 속성과 Action 노드 매칭
            match_props = []
            params = {}
            
            if action_type:
                match_props.append("type: $act_type")
                params['act_type'] = action_type
            
            if target:
                match_props.append("target: $target")
                params['target'] = str(target)
                
            if not match_props:
                return 0.5
                
            props_str = "{" + ", ".join(match_props) + "}"
            
            query = f"""
            MATCH (e:Episode)-[:EXECUTED]->(a:Action {props_str})
            RETURN e.result
            ORDER BY e.timestamp DESC
            LIMIT 5
            """
            
            res = self.graph.query(query, params)
            
            if not res.result_set: return 0.5
            
            valid_results = [r[0] for r in res.result_set] # 'success' or 'failure'
            if not valid_results: return 0.5

            success_count = valid_results.count('success')
            return success_count / len(valid_results)
            
        except Exception as e:
            logging.error(f"[Memory] Query Error: {e}")
            return 0.5

# 싱글톤
memory_manager = FalkorDBManager()
