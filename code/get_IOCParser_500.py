import pandas as pd
import numpy as np 
import requests 
import os 
import re
from tqdm import tqdm 
import fitz 


start_year = 2014 
end_year = 2023
input_file = 'ArticlesDataset_500_Valid.csv'
# 보고서 파일이 저장되어 있을 폴더 목록
file_folder = ['APT_CyberCriminal_Campagin_Collections Reports']
output_file = f'MergedArticles_IOCParsed_New.csv' # IOC 파싱 결과를 저장할 최종 CSV 파일 경로

def main():
    # 1. 데이터 로드
    contents = pd.read_csv(input_file)
    
    # 2. 데이터 클리닝 및 필터링
    # contents.drop([0, 1], inplace=True) # 주석 처리됨 (특정 행 제거)
    contents['Date'] = pd.to_datetime(contents['Date']) # 'Date' 컬럼을 datetime 객체로 변환
    # 지정된 연도 범위 (start_year ~ end_year) 내의 데이터만 필터링
    mask = (contents['Date'].dt.year >= start_year) & (contents['Date'].dt.year <= end_year)
    contents = contents.loc[mask]
    contents.reset_index(drop=True, inplace=True) # 필터링 후 인덱스 재설정
    
    # # 3. PDF 파일 다운로드
    # get_pdfs(start_year, end_year, contents)
    
    # 4. 소스 파일 로드 (현재 get_data 내부에서 사용되지 않음)
    # with open('sources.txt', 'r') as f:
    #     initial_sources = f.read().split('\n')
        
    # 5. PDF에서 텍스트 추출 및 IOC 데이터 파싱
    # [오류 가능성]: get_data 함수 내부에서 extract_data_from_text(text, year) 호출 시 인자 불일치
    cve, mitre, yara = get_data(start_year, end_year, contents)
     
    # 6. 결과를 DataFrame에 추가
    contents["CVE"] = cve
    contents["MITRE"] = mitre
    contents["YARA"] = yara

    # 7. 최종 결과를 CSV 파일로 저장
    contents.to_csv(output_file, index=False)
    

def get_data(start_year, end_year, contents):
    # [주의]: start_year, end_year, initial_sources는 현재 함수 내부에서 사용되지 않음.
    
    cve_list = []
    mitre_list = []
    yara_list = []
    
    # DataFrame의 모든 기사에 대해 반복
    for i in (progress_bar := tqdm(range(0, len(contents)))):
        progress_bar.set_description("Extracting data from PDF")
        year = contents['Date'][i].year
        
        # [오류 방지] PDF 텍스트가 추출되지 않았을 경우를 대비하여 초기화
        text = "" 
        
        # 파일이 존재할 수 있는 모든 폴더를 탐색
        for folder in file_folder:
            try:
                # 현재 보고서의 예상 파일 경로 구성
                document = f'./Reports/{folder}/{year}/{contents["Filename"][i]}.pdf'
                
                # 파일이 실제로 존재하면 텍스트 추출 시작
                if os.path.exists(document):
                    text = extract_text_from_pdf(document)
                    break  # 파일 발견 및 텍스트 추출 완료, 폴더 탐색 종료
            except Exception as e:
                # 텍스트 추출 중 오류가 발생하면 (매우 드물게) 출력하고 다음 폴더로 이동
                print(f"Error extracting text from {document}: {e}")
                continue
        
        # 추출된 텍스트를 사용하여 IOC API 호출
        # [오류 가능성]: extract_data_from_text 함수는 인자가 'text' 하나만 필요하지만,
        #              여기서는 'year'도 전달하려고 하고 있음. (extract_data_from_text(text, year))
        #              extract_data_from_text 함수 정의를 수정하거나 'year'를 제거해야 함.
        cve, mitre, yara = extract_data_from_text(text, year) 
        
        # 결과를 각 리스트에 추가
        cve_list.append(cve)
        mitre_list.append(mitre)
        yara_list.append(yara)
        
    return cve_list, mitre_list, yara_list

def clean_output(list_str):
    """
    IOC 파싱 결과 문자열을 정리하는 함수. 현재는 main 함수에서 사용되지 않음.
    파싱된 리스트 형태의 문자열을 쉼표로 구분된 깔끔한 문자열로 변환합니다.
    """
    # Check if the entry is NaN or empty
    if pd.isna(list_str) or list_str.strip() == "":
        return ""  # Return empty string if no information
    
    # Remove unwanted characters and split by commas or newline
    list_orig = list_str.replace('\n', '').replace("'", "").replace("[", "").replace("]", "").split(", ")
    # Rejoin as a comma-separated string
    cleaned_list = ", ".join(list_orig).strip()
    return cleaned_list

'''
def extract_dates_from_text(text, publish_date):
    # 이 함수는 현재 주석 처리되어 사용되지 않음 (날짜 추출 로직)
    date_patterns = [
        r'\b\d{4}\b',  # Matches years (e.g., 2013, 2014)
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',  # "Month YYYY"
        r'\b(?:Spring|Summer|Autumn|Fall|Winter)\s+\d{4}\b',  # "Season YYYY"
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # "DD/MM/YYYY" or "MM-DD-YYYY"
        r'\b(?:Late|Early|Middle)\s+\w+\s+\d{4}\b'  # "Late October 2014"
    ]
    combined_pattern = "|".join(date_patterns)
    extracted_dates = re.findall(combined_pattern, text)

    # Extract years from the matched dates
    years = []
    for date in extracted_dates:
        # Check for YYYY format in extracted data
        year_match = re.search(r'\b\d{4}\b', date)
        if year_match:
            year = int(year_match.group())
            if 2000 <= year <= publish_date:  # Filter years between 2010 and publish_date
                years.append(year)
    
    return sorted(set(years))
'''

# [오류 가능성]: 이 함수는 'text' 인자만 받도록 정의되어 있지만, get_data에서 'year' 인자도 함께 전달받으려 하고 있음.
# get_IOCParser.py (수정된 extract_data_from_text 함수)

# [주의]: get_data에서 year 인자를 전달하고 있으므로, 함수 정의에 year를 유지했습니다.
def extract_data_from_text(text, year): 
    """
    텍스트에서 IOC(침해지표)를 추출하기 위해 IOCParser API에 요청을 보냅니다.
    """
    payload = text 
    url = "https://api.iocparser.com/raw"
    headers = {
    'Content-Type': 'text/plain' 
    }

    # API 요청: text/plain이므로 'data=payload' 사용
    # json=payload는 payload를 JSON 형식으로 직렬화하려 시도하므로 부적절할 수 있습니다.
    response = requests.request("POST", url, headers=headers, data=payload)
        
    # --- 1. 상태 코드별 처리 ---
    
    if response.status_code == 204:
        # 204 (No Content): 데이터 없음
        print("API 응답: 204 No Content. 해당 텍스트에서 IOC를 찾을 수 없습니다.")
        return [], [], [] # 즉시 빈 리스트 반환 및 함수 종료

    if response.status_code >= 400:
        # 4xx (Client Error) 또는 5xx (Server Error)
        print(f"HTTP 요청 실패! 상태 코드: {response.status_code}")
        print("서버 오류 메시지:", response.text[:500])
        return [], [], [] # 즉시 빈 리스트 반환 및 함수 종료
        
    # 200 (OK)인 경우 처리
    if response.status_code == 200:
        try:
            # 성공적으로 JSON 데이터가 있을 때 추출
            data = response.json()['data']
            # API 문서에 따라 키 값 확인 (기존 코드와 통일성을 위해 수정하지 않음)
            cve = data.get('CVE', [])
            mitre = data.get('MITRE_ATT&CK', [])
            yara = data.get('YARA_RULE', [])
            
            
            # response = requests.request("POST", url, headers=headers, json=payload)
            # print(response.json()['data'])
            # cve = response.json()['data']['CVE']
            # mitre = response.json()['data']['MITRE_ATT&CK']
            # yara = response.json()['data']['YARA_RULE']
            
            return cve, mitre, yara
            
        except requests.exceptions.JSONDecodeError as e:
            # 200이지만 응답 본문이 깨졌을 경우를 위한 안전 장치
            print(f"JSON 디코딩 오류 발생 (200 상태): {e}")
            print("응답 텍스트 미리보기:", response.text[:200])
            return [], [], [] 
    
    # [불필요한 코드 제거]: 아래 코드는 위의 if/elif/if/except 블록 이후에 도달할 수 없으므로 제거
    # cve = response.json()['data']['CVE']
    # mitre = response.json()['data']['MITRE_ATTACK']
    # yara = response.json()['data']['YARA_RULE']
    # return cve, mitre, yara
    
    # 위의 모든 조건을 통과했지만 200이 아닌 예외적인 경우를 대비하여 추가 (선택 사항)
    return [], [], [] # 안전 장치

def get_pdfs(start_year, end_year, contents):       
    """
    DataFrame에 있는 'Download Url'을 사용하여 PDF 파일을 다운로드하고 저장합니다.
    이미 파일이 존재하는지 확인하여 중복 다운로드를 방지합니다.
    """
    for i in (progress_bar := tqdm(range(len(contents)))):
        year = contents['Date'][i].year
        
        # 지정된 연도 범위 내에서만 다운로드 진행
        if start_year <= year <= end_year:
            filename = contents['Filename'][i]
            file_found = False
            
            # 파일이 존재할 수 있는 폴더를 순회하며 확인
            for folder in file_folder:
                directory = f'./Reports/{folder}/{year}'
                file_path = f'{directory}/{filename}.pdf'
                
                if os.path.exists(file_path):
                    file_found = True
                    break # 파일 발견 시 순회 종료
            
            # 파일이 존재하지 않는 경우에만 다운로드 수행
            if not file_found:
                # 파일을 저장할 디렉토리가 없으면 생성
                if not os.path.exists(directory):
                    # [주의]: 여기서 'directory'는 마지막 순회 폴더 기준으로 생성되므로,
                    #         file_folder 목록 중 첫 번째 폴더에 저장될 것입니다.
                    os.makedirs(directory)

                # PDF 다운로드 및 저장
                response = requests.get(contents['Download Url'][i])
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
        progress_bar.set_description('Downloading PDF articles')

def extract_text_from_pdf(filename):
    """
    PyMuPDF (fitz) 라이브러리를 사용하여 PDF 파일에서 텍스트를 추출합니다.
    """
    text = ""
    try:
        doc = fitz.open(filename)
        for page in doc:
            text += page.get_text() # 페이지별 텍스트를 누적
        return text
    except:
        # PDF 파일이 손상되었거나 열 수 없는 경우 빈 문자열 반환
        return text

if __name__ == "__main__":
    main()