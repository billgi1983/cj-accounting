import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
from datetime import datetime


scopes = ["https://spreadsheets.google.com/feeds"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["cjson"], scopes)
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(st.secrets["sheet_key"])
sheet_1 = spreadsheet.sheet1
usernames = [user for user in st.secrets["credential"]["usernames"].keys()]
info_type = st.secrets["info_type"].split(",")
relative_coord = st.secrets["relative_coord"]


# ----- functions ----- #

# 計算現在年月
today = datetime.now()
year, month = today.year, today.month


# 計算應該要操作哪一基礎列
def get_row_init(year: int, month: int) -> int:
  year_base = 2023
  month_base = 9
  return (((year - year_base)*12) + (month - month_base)) * 5 + 2


def get_info(row_init: int, target: str):
  row = row_init + int(relative_coord[target].split(',')[0])
  col = int(relative_coord[target].split(',')[1])
  return sheet_1.cell(row, col).value


def get_cell_formula(row_init: int, target: str):
  row = row_init + int(relative_coord[target].split(',')[0])
  col = int(relative_coord[target].split(',')[1])
  return sheet_1.cell(row, col, value_render_option='FORMULA').value

def set_cell_value(row_init: int, target: str, money: str):
  row = row_init + int(relative_coord[target].split(',')[0])+1
  col = int(relative_coord[target].split(',')[1])-4
  sheet_1.update_cell(row, col, money)

  row = row_init + int(relative_coord[target].split(',')[0])+1
  col = int(relative_coord[target].split(',')[1])
  sheet_1.update_cell(row, col, money)


def set_cell_formula(row_init: int, target: str, math_type: str, money: str):
  row = row_init + int(relative_coord[target].split(',')[0])
  col = int(relative_coord[target].split(',')[1])
  origin = get_cell_formula(row_init, target)
  sheet_1.update_cell(row, col, origin + math_type + money)

  set_cell_value(row_init, "H0", get_info(row_init, "H0"))
  set_cell_value(row_init, "H1", get_info(row_init, "H1"))
  #set_cell_value(row_init, "H2", get_info(row_init, "H2"))
  #set_cell_value(row_init, "H3", get_info(row_init, "H3"))
  #set_cell_value(row_init, "H4", get_info(row_init, "H4"))


def deposit(row_init: int, target: str, money: str):
  set_cell_formula(row_init, target, '+',  money)



def spend(row_init: int, target: str, money: str):
  set_cell_formula(row_init, target, '-', money)


def transfer(row_init: int, target: str, money: str):
  set_cell_formula(row_init, target, '+', money)



# ----- streamlit ----- #

if "login" not in st.session_state:
  st.session_state.login = False
if 'info' not in st.session_state:
  st.session_state.info = []
if 'action_type' not in st.session_state:
  st.session_state.action_type = "消費"
if 'target' not in st.session_state:
  st.session_state.target = None
if 'row_init' not in st.session_state:
  st.session_state.row_init = None
if 'money' not in st.session_state:
  st.session_state.money = '0'


def check_login(username_, password_):
  if username_ not in usernames:
    return False
  if password_ == st.secrets["credential"]["usernames"][username_]["password"]:
    return True
  else:
    return False


def login_page():
  lg_left, lg_middle, lg_right = st.columns((1, 3, 1))
  with lg_middle:
    st.title("登入頁面")
    username = st.text_input("請輸入帳號")
    password = st.text_input("請輸入密碼", type="password")
    login_button = st.button("登入")

    if login_button:
      if check_login(username, password):
        st.success("Loading")
        st.session_state.login = True
        st.session_state.row_init = get_row_init(year, month)
        st.session_state.info = [get_info(st.session_state.row_init, i) for i in info_type]
        st.experimental_rerun()
      else:
        st.error("帳號或密碼錯誤")

def main_page():
  st.session_state.action_type = st.radio("行為：", ["消費", "轉帳", "存入"], horizontal=True)

  if st.session_state.action_type == "消費":
    st.session_state.target = st.radio("消費：", st.secrets["spend"].split(','), index=0, horizontal=True)
  elif st.session_state.action_type == "轉帳":
    st.session_state.target = st.radio("轉帳：", st.secrets["transfer"].split(','), index=0, horizontal=True)
  elif st.session_state.action_type == "存入":
    st.session_state.target = st.radio("存入：", [st.secrets["deposit"]], index=0, horizontal=True)

  money = st.text_input('金額', key="money_text")


  def clear_text():
    if st.session_state.action_type == "消費":
      spend(st.session_state.row_init, st.session_state.target, st.session_state.money)
    elif st.session_state.action_type == "轉帳":
      transfer(st.session_state.row_init, st.session_state.target, st.session_state.money)
    elif st.session_state.action_type == "存入":
      deposit(st.session_state.row_init, st.session_state.target, st.session_state.money)

    st.session_state.money = ''
    st.session_state.info = [get_info(st.session_state.row_init, i) for i in info_type]
    st.session_state["money_text"] = ""
    send = False
    
  if money == '':
    st.session_state.money = '0'
  else:
    st.session_state.money = money

  now_state = get_info(st.session_state.row_init, st.session_state.target)
  st.write(f"{st.session_state.target} 現值為：{now_state} \n您要{st.session_state.action_type} {st.session_state.money}元")
  send  = st.button("提交", on_click=clear_text)

  st.write(f"{info_type[0]}：{st.session_state.info[0]}")
  st.write(f"{info_type[1]}：{st.session_state.info[1]}")
  st.write(f"{info_type[3]}：{st.session_state.info[3]}")
  st.write(f"{info_type[4]}：{st.session_state.info[4]}")
  st.write(f"{info_type[5]}：{st.session_state.info[5]}")
  st.write(f"{info_type[6]}：{st.session_state.info[6]}")
  st.write(f"{info_type[2]}：{st.session_state.info[2]}")
  st.write(f"{info_type[7]}：{st.session_state.info[7]}")
  st.write(f"{info_type[8]}：{st.session_state.info[8]}")


# 主程式
def main():
  st.set_page_config(page_title="Cash-Flow", page_icon="💸", layout="centered", initial_sidebar_state="collapsed")

  if not st.session_state.login:
    login_page()
  else:
    main_page()


if __name__ == "__main__":
  main()
