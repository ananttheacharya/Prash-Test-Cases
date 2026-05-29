def test_button():
    expected = 'Submit'
    received = 'Click me'
    assert expected == received, f'Expected {expected} but got {received}'

test_button()