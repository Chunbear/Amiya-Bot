import jieba

from modules.commonMethods import Reply, word_in_sentence, remove_punctuation
from database.baseController import BaseController
from functions.operator.materialsCosts import MaterialCosts
from functions.operator.operatorInfo import OperatorInfo

voices = [
    "任命助理", "任命队长", "编入队伍", "问候", "闲置",
    "交谈1", "交谈2", "交谈3", "晋升后交谈1", "晋升后交谈2",
    "信赖提升后交谈1", "信赖提升后交谈2", "信赖提升后交谈3",
    "精英化晋升1", "精英化晋升2",
    "行动出发", "行动失败", "行动开始", "3星结束行动", "4星结束行动", "非3星结束行动",
    "选中干员1", "选中干员2", "部署1", "部署2", "作战中1", "作战中2", "作战中3", "作战中4",
    "戳一下", "信赖触摸", "干员报到", "进驻设施", "观看作战记录", "标题"
]
voices_keywords = []
for key in voices:
    voices_keywords.append('%s 100 n' % key)

print('loading operators data...')
database = BaseController()
material_costs = MaterialCosts(voices_keywords)
operator = OperatorInfo()
jieba.load_userdict('resource/operators.txt')
jieba.load_userdict('resource/stories.txt')


class Init:
    def __init__(self):
        self.function_id = 'checkOperator'
        self.keyword = voices + material_costs.keywords
        self.stories_title = list(operator.stories_title.keys()) + [i for k, i in operator.stories_title.items()]

    def action(self, data):

        message = data['text_digits']
        message_ori = remove_punctuation(data['text'])

        words = jieba.lcut_for_search(
            (message.lower() + message_ori.lower()).replace(' ', '')
        )

        name = ''
        level = 0
        skill = ''
        voice_key = ''
        skill_index = 0
        stories_key = ''

        for item in words:
            # 获取档案关键词
            if item in self.stories_title:
                stories_key = item
                continue
            # 获取语音关键词
            if item in voices:
                voice_key = item
                continue
            # 获取干员名
            if item in material_costs.operator_map:
                name = material_costs.operator_map[item]
                continue
            if item in material_costs.operator_list:
                name = item
                continue
            # 获取专精或精英等级
            if item in material_costs.level_list:
                level = material_costs.level_list[item]
                continue
            # 获取技能序号
            if item in material_costs.skill_index_list:
                skill_index = material_costs.skill_index_list[item]
                continue
            # 获取技能名
            if item in material_costs.skill_map:
                skill = material_costs.skill_map[item]
                continue

        if name == '' and skill == '':
            return Reply('博士，想查询哪位干员的资料呢？')

        if level != 0:
            if level < 0:
                # todo 精英化资料
                level = abs(level)
                result = material_costs.check_evolve_costs(name, level)
            else:
                if level >= 8 and '材料' in message:
                    # todo 专精资料
                    level -= 7
                    result = material_costs.check_mastery_costs(name, skill, level, skill_index=skill_index)
                else:
                    # todo 技能数据
                    result = operator.get_skill_data(name, skill, level, skill_index=skill_index)
            return Reply(result)

        if name:
            # todo 档案资料
            if stories_key:
                story = database.operator.find_operator_stories(name, stories_key)
                if story:
                    text = '博士，这是干员%s的《%s》档案\n\n' % (name, stories_key)
                    return Reply(text + story['story_text'])
                else:
                    return Reply('博士，没有找到干员%s的《%s》档案' % (name, stories_key))

            # todo 语音资料
            if voice_key:
                return self.find_voice(name, voice_key)

            if word_in_sentence(message, ['精英', '专精']):
                return Reply('博士，要告诉阿米娅精英或专精等级哦')

            if word_in_sentence(message, ['语音']):
                return Reply('博士，要告诉阿米娅语音的详细标题哦')

            if skill or skill_index:
                return Reply('博士，要查询干员技能资料的话，请加上【技能等级】或者加上【技能等级和“材料”关键字】哦')

            return Reply(operator.get_detail_info(name))

    @staticmethod
    def find_voice(name, voice):
        result = database.operator.find_operator_voice(name, voice)
        if result:
            text = '博士，为您找到干员%s的语音档案：\n\n【%s】\n%s' % (name, voice, result['voice_text'])
            return Reply(text)
        return Reply('抱歉博士，没有找到干员%s%s相关的语音档案' % (name, voice))
