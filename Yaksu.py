import discord
from discord.ext import commands, tasks
import datetime

intents = discord.Intents.default()
intents.voice_states = True  # 음성 상태를 감지하기 위한 권한

bot = commands.Bot(command_prefix="!", intents=intents)

# 유저의 음성 채널 입장 및 퇴장 시간을 저장하는 딕셔너리
user_voice_times = {}
# 유저별 누적 시간을 저장하는 딕셔너리
user_total_times = {}

# 로그를 남길 채널 ID를 저장하는 변수 (초기값은 수동 설정)
log_channel_id = 1286196292644507669  # 채널 ID를 여기에 수동으로 입력

# 음성 채널 입장 감지
@bot.event
async def on_voice_state_update(member, before, after):
    global log_channel_id
    if log_channel_id is None:
        return  # 로그 채널이 설정되지 않은 경우 아무것도 하지 않음
    
    log_channel = bot.get_channel(log_channel_id)  # 로그를 기록할 채널 가져오기

    if log_channel is None:
        return
    
    # 로그 채널에서 읽기 권한이 있는 사람을 필터링
    def can_read_channel(user):
        permissions = log_channel.permissions_for(user)
        return permissions.read_messages

    # 유저가 음성 채널에 들어갔을 때
    if before.channel is None and after.channel is not None:
        # 만약 사용자가 로그 채널을 읽을 권한이 없다면 무시
        if not can_read_channel(member):
            return

        user_voice_times[member.id] = {"join_time": datetime.datetime.now(), "leave_time": None}
        join_time = user_voice_times[member.id]['join_time'].strftime('%Y-%m-%d %H:%M:%S')  # 시간을 원하는 포맷으로 변환

        # 현재 음성 채널에 있는 모든 멤버들 가져오기
        members_in_channel = after.channel.members
        members_names = ', '.join([m.display_name for m in members_in_channel])

        # 사용자가 들어간 음성 채널 이름 추가
        message = (
            f"------------------------------------------------------------------------\n"
            f"🔊 **{member.display_name}**님께서 **[{after.channel.name}]** 채널에 들어오셨습니다.\n"
            f"👥 현재 음성 채널에 있는 멤버들: {members_names}\n"
            f"------------------------------------------------------------------------"
        )
        print(message)  # 콘솔 출력
        if log_channel:
            await log_channel.send(message)  # 로그 채널에 메시지 보내기

    # 유저가 음성 채널을 떠났을 때
    elif before.channel is not None and after.channel is None:
        # 만약 사용자가 로그 채널을 읽을 권한이 없다면 무시
        if not can_read_channel(member):
            return

        if member.id in user_voice_times and user_voice_times[member.id]["join_time"] is not None:
            user_voice_times[member.id]["leave_time"] = datetime.datetime.now()
            join_time = user_voice_times[member.id]["join_time"]
            leave_time = user_voice_times[member.id]["leave_time"]

            # 시간을 원하는 포맷으로 변환
            join_time_str = join_time.strftime('%Y-%m-%d %H:%M:%S')  # 입장 시간
            leave_time_str = leave_time.strftime('%Y-%m-%d %H:%M:%S')  # 퇴장 시간

            # 총 머문 시간 계산 (분 단위로 변환)
            duration = leave_time - join_time
            total_minutes = divmod(duration.total_seconds(), 60)[0]  # 총 머문 시간을 분 단위로 변환

            # 유저의 누적 시간 업데이트
            if member.id not in user_total_times:
                user_total_times[member.id] = 0  # 첫 누적 시간 초기화
            user_total_times[member.id] += total_minutes  # 누적 시간에 더하기

            # 퇴장할 때 남은 멤버들 목록
            remaining_members = before.channel.members
            remaining_members_names = ', '.join([m.display_name for m in remaining_members]) if remaining_members else "없음"

            # 사용자가 나간 음성 채널 이름 추가
            message = (
                f"------------------------------------------------------------------------\n"
                f"🔴 **{member.display_name}**님께서 **[{before.channel.name}]** 채널에서 나가셨습니다.\n"
                f"🕒 입장 날짜-시간: {join_time_str}\n"
                f"🕒 퇴장 날짜-시간: {leave_time_str}\n"
                f"⏳ 총 머문시간: {total_minutes} 분\n"
                f"📊 이번 주 누적 시간: {user_total_times[member.id]} 분\n"
                f"👥 퇴장 후 남아있는 멤버들: {remaining_members_names}\n"
                f"------------------------------------------------------------------------"
            )

            print(message)  # 콘솔 출력
            if log_channel:
                await log_channel.send(message)  # 로그 채널에 메시지 보내기
            
            # 딕셔너리에서 삭제
            del user_voice_times[member.id]

# 매주 월요일 오전 11시에 누적 시간을 초기화하는 함수
@tasks.loop(time=datetime.time(hour=11, minute=0, second=0))
async def reset_weekly_totals():
    global user_total_times
    log_channel = bot.get_channel(log_channel_id)
    
    # 누적 시간 초기화 메시지 출력
    if log_channel:
        await log_channel.send("⏳ **이번 주 누적 시간**이 월요일 11시를 기준으로 초기화되었습니다.")
    
    # 누적 시간 초기화
    user_total_times = {}

# 봇 시작 시 초기화 타이머 실행
@bot.event
async def on_ready():
    reset_weekly_totals.start()  # 매주 월요일 오전 11시에 누적 시간 초기화

# 봇 시작
bot.run('Tc')
