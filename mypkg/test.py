from models.context import Context
from models.code_info import CodeInfo
from mypkg.db_settings import Base, engine, session

def main():
    Base.metadata.create_all(engine)
    test_context = Context('hello')
    session.add(test_context)
    session.commit()
    test_context = Context.query.first()
    code_info = CodeInfo(1, 'hello', test_context.id)
    session.add(code_info)
    session.commit()
    print(test_context.code_infos[0].code)

if __name__ == '__main__':
    main()
