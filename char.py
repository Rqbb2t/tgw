import re
import json
import os

def clean_text(text):
    """§색상코드 제거 및 공백 정리"""
    if not isinstance(text, str): return text
    return re.sub(r'§.', '', text).strip()

def strip_brackets(text):
    """중괄호 {}를 완전히 제거하여 알맹이만 추출"""
    if not isinstance(text, str): return text
    return text.replace('{', '').replace('}', '')

def parse_skill_file(skill_code, skill_dir="./"):
    """캐릭터 code에 해당하는 스킬 파일을 읽어 객체 리스트로 반환"""
    file_path = os.path.join(skill_dir, f"{skill_code}.yml")
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    raw_data = {}
    for line in content.splitlines():
        if ':' in line and not line.startswith('//'):
            k, v = line.split(':', 1)
            raw_data[k.strip()] = v.strip()

    skill_groups = {}
    for key, value in raw_data.items():
        match = re.match(r'skill(\d+)(.*)', key)
        if match:
            num = int(match.group(1))
            suffix = match.group(2)
            if num not in skill_groups: skill_groups[num] = {}
            skill_groups[num][suffix] = value

    skills = []
    for num in sorted(skill_groups.keys()):
        group = skill_groups[num]
        s_obj = {}
        lore_list = []
        
        # 1. 일반 속성 처리
        for suffix, val in group.items():
            clean_val = clean_text(val)
            if suffix == "": 
                s_obj["name"] = clean_val
            elif suffix == "_cooldown": 
                # 쿨다운도 {값} 형태로 유지
                s_obj["cooldown"] = f"{{{strip_brackets(clean_val)}}}"
            elif not suffix.startswith("_lore"):
                attr = suffix[1:]
                try:
                    s_obj[attr] = float(clean_val) if '.' in clean_val else int(clean_val)
                except: 
                    s_obj[attr] = clean_val

        # 2. Lore 변수 치환 (결과를 {값} 형태로 감쌈)
        l_keys = sorted([k for k in group.keys() if re.match(r'^_lore_?\d+$', k)])
        
        for l_key in l_keys:
            base_lore = clean_text(group[l_key])
            # {} 안의 변수명을 찾아 실제 데이터로 치환
            for var in re.findall(r'\{(.*?)\}', base_lore):
                var_key = f"{l_key}_{var}"
                if var_key in group:
                    # 데이터의 {}를 제거한 후 다시 {}로 감쌈
                    val_content = strip_brackets(clean_text(group[var_key]))
                    base_lore = base_lore.replace(f"{{{var}}}", f"{{{val_content}}}")
                else:
                    # 매칭 변수 없어도 중괄호 정리
                    base_lore = base_lore.replace(f"{{{var}}}", f"{{{strip_brackets(var)}}}")
            
            lore_list.append(base_lore)
            
        s_obj["lore"] = lore_list
        skills.append(s_obj)
        
    return skills

def main_processor(char_file_path, output_json_path, skill_dir="./"):
    if not os.path.exists(char_file_path):
        print(f"❌ {char_file_path} 파일이 없습니다.")
        return

    with open(char_file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    r_map = dict(re.findall(r'range(\d+):([^\n]+)', text))
    a_map = dict(re.findall(r'attacktype(\d+):([^\n]+)', text))
    c_map = dict(re.findall(r'chartype(\d+):([^\n]+)', text))

    final_data = {}
    char_ids = sorted(list(set(re.findall(r'^\s*(\d+):', text, re.MULTILINE))), key=int)

    for cid in char_ids:
        char_entry = {}
        char_lore = []
        
        name_match = re.search(rf'^\s*{cid}:(.+)', text, re.MULTILINE)
        if name_match: char_entry["name"] = clean_text(name_match.group(1))

        properties = re.findall(rf'^\s*{cid}_([^:]+):(.+)', text, re.MULTILINE)
        for key, val in properties:
            key, val = key.strip(), val.strip()
            if key == 'code':
                char_entry['code'] = val
                char_entry['skills'] = parse_skill_file(val, skill_dir)
            elif key == 'type':
                types = []
                for t in val.split(','):
                    t = t.strip()
                    if t.startswith('r'): types.append(clean_text(r_map.get(t[1:], t).split(':')[0]))
                    elif t.startswith('a'): types.append(clean_text(a_map.get(t[1:], t).split(':')[0]))
                    elif t.startswith('c'): types.append(clean_text(c_map.get(t[1:], t).split(':')[0]))
                char_entry[key] = types
            elif key == 'stat':
                char_entry[key] = {s.split(':')[0].strip(): (float(s.split(':')[1]) if '.' in s.split(':')[1] else int(s.split(':')[1])) 
                                  for s in val.split(',') if ':' in s}
            elif key.startswith('lore'):
                char_lore.append(clean_text(val))
            else:
                try: char_entry[key] = float(val) if '.' in val else int(val)
                except: char_entry[key] = val

        if char_lore: char_entry["lore"] = char_lore
        final_data[cid] = char_entry

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)
    
    print(f"✅ 병합 완료: {output_json_path}")

if __name__ == "__main__":
    main_processor('chars.yml', 'characters.json')