import sys
import os

class TerminalTee:
    """
    터미널과 로그 파일 양쪽에 메시지를 전달하는 역할을 수행합니다.
    Streamlit 환경에서 발생할 수 있는 속성 오류를 방지하도록 설계되었습니다.
    """
    def __init__(self, log_file, original_terminal=None):
        # 메시지를 기록할 파일 객체입니다.
        self.log_file = log_file
        # 기존 터미널 객체입니다. 없을 경우 sys.__stdout__을 사용합니다.
        self.terminal = original_terminal if original_terminal else sys.__stdout__

    def write(self, message):
        """
        메시지를 터미널과 파일에 각각 기록합니다.
        """
        # 터미널 객체가 존재할 경우에만 터미널에 기록을 시도합니다.
        if hasattr(self, 'terminal') and self.terminal is not None:
            try:
                self.terminal.write(message)
            except Exception:
                # 스트림릿 환경에서 터미널 쓰기 실패 시 무시합니다.
                pass
        
        # 로그 파일에 메시지를 기록합니다.
        if self.log_file:
            self.log_file.write(message)

    def flush(self):
        """
        버퍼에 남아있는 내용을 강제로 출력합니다.
        """
        if hasattr(self, 'terminal') and self.terminal is not None:
            try:
                self.terminal.flush()
            except Exception:
                pass
        
        if self.log_file:
            self.log_file.flush()

def setup_terminal_logging(log_dir="logs"):
    """
    시스템의 표준 출력을 TerminalTee로 교체하여 로그를 기록합니다.
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_path = os.path.join(log_dir, "system.log")
    log_file = open(log_path, "a", encoding="utf-8")
    
    # 현재의 표준 출력을 가져와 TerminalTee를 생성합니다.
    sys.stdout = TerminalTee(log_file, sys.stdout)
    print(f"[INFO] Logging initialized at: {log_path}")