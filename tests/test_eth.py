import io

from eth import EthInterpreter


def run(source, answers=None):
    output = []
    answers = iter(answers or [])
    interpreter = EthInterpreter(input_fn=lambda _prompt="": next(answers), output_fn=output.append)
    interpreter.run(source)
    return output


def test_print_and_arithmetic():
    assert run('x = 10\ny = 20\nአሳይ x + y') == [30]


def test_string_concatenation():
    assert run('ስም = "ሱራፌል"\nአሳይ "ሰላም " + ስም') == ["ሰላም ሱራፌል"]


def test_if_else():
    source = '''x = 10\nከሆነ x >= 18:\n    አሳይ "አዋቂ"\nካልሆነ:\n    አሳይ "ልጅ"'''
    assert run(source) == ["ልጅ"]


def test_repeat():
    assert run('ድገም 3:\n    አሳይ "Eth"') == ["Eth", "Eth", "Eth"]


def test_input_expression():
    assert run('ስም = ጠይቅ("ስምህ?")\nአሳይ "ሰላም " + ስም', ["ሱራፌል"]) == ["ሰላም ሱራፌል"]
