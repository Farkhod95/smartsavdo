def enum_serialize(enum_choices):
    return [{'key': key, 'value': value} for key, value in enum_choices]