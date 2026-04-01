import re
import json
import os

def parse_and_merge_files(file_list, output_filename):
    combined_data = {}
    # 정규표현식: (ID) _ (속성명) (숫자) : (값)
    pattern = re.compile(r"(\d+)_([a-zA-Z]+)(\d*):(.*)")

    for file_path in file_list:
        if not os.path.exists(file_path):
            print(f"경고: {file_path} 파일을 찾을 수 없습니다.")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                
                match = pattern.match(line)
                if match:
                    raw_id = match.group(1)
                    key_base = match.group(2)
                    value = match.group(4).strip()

                    if not value:
                        continue

                    # 1. ID 및 Tier 처리 (ID의 첫 번째 자리 추출)
                    item_id_int = int(raw_id)
                    tier = item_id_int // 1000  # 예: 1003 // 1000 = 1
                    
                    if raw_id not in combined_data:
                        combined_data[raw_id] = {"tier": tier}

                    # 2. 데이터 타입 변환
                    parsed_value = value
                    if value.lower() == "true": parsed_value = True
                    elif value.lower() == "false": parsed_value = False
                    elif value.isdigit(): parsed_value = int(value)

                    # 3. 속성별 분류 저장
                    # lore 리스트 처리
                    if key_base == "lore":
                        if "lore" not in combined_data[raw_id]:
                            combined_data[raw_id]["lore"] = []
                        combined_data[raw_id]["lore"].append(parsed_value)
                    
                    # mix 리스트 처리 (내부 값 int 변환)
                    elif key_base == "mix":
                        mix_raw = [i.strip() for i in value.split(',') if i.strip()]
                        combined_data[raw_id]["mix"] = [int(i) if i.isdigit() else i for i in mix_raw]

                    # 기타 속성
                    else:
                        combined_data[raw_id][key_base] = parsed_value

    # JSON 저장
    with open(output_filename, 'w', encoding='utf-8') as out_file:
        json.dump(combined_data, out_file, indent=4, ensure_ascii=False)
    
    print(f"성공: {len(combined_data)}개의 아이템이 '{output_filename}'에 병합되었습니다.")

# 실행
files = ['tier1.yml', 'tier2.yml', 'tier3.yml']
parse_and_merge_files(files, 'total_items.json')