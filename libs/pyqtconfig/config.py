# -*- coding: utf-8 -*-
''' PyQtConfig is a simple API for handling, persisting and synchronising
    configuration within PyQt applications.
'''
import logging

import types
from collections import OrderedDict

# Import PyQt5/PySide2 classes
from .qt import (QComboBox, QCheckBox, QAction,
                 QActionGroup, QPushButton, QSpinBox,
                 QDoubleSpinBox, QPlainTextEdit, QLineEdit,
                 QListWidget, QSlider, QButtonGroup,
                 QTabWidget, QVariant, Qt, QMutex, QMutexLocker, QSettings,
                 QObject, Signal)

# xml.etree.ElementTree模块实现了一个简单而高效的API用于解析和创建XML数据
# 尽量使用 C 语言实现的那种，因为它速度更快，而且消耗的内存更少
# 从文件或者字符串中解析到xml的结构、查找元素、修改元素
try:
    import xml.etree.cElementTree as et
except ImportError:
    import xml.etree.ElementTree as et

# 重新计算全局 or 重新计算视图 ？？？
RECALCULATE_ALL = 1
RECALCULATE_VIEW = 2

# 动态添加实例方法
def types_MethodType(fn, handler):
    try:
        # 查看变量handler的类型
        # types.MethodType():第一个参数是要绑定的方法，第二个参数是要绑定的对象，第三个参数是类名（可省略），
        # 返回值指向绑定的方法的函数代码，只要使用这个返回值，就可以当做是调用了对象的方法
        return types.MethodType(fn, handler, type(handler))
    except TypeError:
        return types.MethodType(fn, handler)

# 提取传入对象vs中符合匹配规则的数据，并将文本内容赋值给v，
# 若这些数据类型中包括CONVERT_TYPE_FROM_XML中列举的类型，则更改赋值，所有的v被添加到l，l为返回值
def _convert_list_type_from_XML(vs):
    '''
    Lists are a complex type with possibility for mixed sub-types. Therefore
    each sub-entity must be wrapped with a type specifier.
    '''
    # ConfigListItem is legacy

    # findall(匹配规则，原始文档)，返回一个所有匹配的子元素列表
    # ListItem与ConfigListItem有何意义？？？
    vlist = vs.findall('ListItem') + vs.findall('ConfigListItem')
    l = []
    for xconfig in vlist:
        v = xconfig.text
        if xconfig.get('type') in CONVERT_TYPE_FROM_XML:
            # Recursive; woo!
            v = CONVERT_TYPE_FROM_XML[xconfig.get('type')](xconfig)
        l.append(v)
    return l

# 在co父节点上新建子节点并设置其类型，最后进行格式转换，转换成xml
def _convert_list_type_to_XML(co, vs):
    '''
    Lists are a complex type with possibility for mixed sub-types. Therefore
    each sub-entity must be wrapped with a type specifier.
    '''
    for cv in vs:
        # SubElement（父元素、子元素名称）：创建一个元素实例，并将其附加到现有元素
        # 在父节点co上新建子节点，其名称为ListItem
        c = et.SubElement(co, "ListItem")
        t = type(cv).__name__
        c.set("type", t)
        c = CONVERT_TYPE_TO_XML[t](c, cv)
    return co


def _convert_dict_type_from_XML(vs):
    '''
    Dicts are a complex type with possibility for mixed sub-types. Therefore
    each sub-entity must be wrapped with a type specifier.
    '''
    vlist = vs.findall('DictItem')
    d = {}
    for xconfig in vlist:
        v = xconfig.text
        if xconfig.get('type') in CONVERT_TYPE_FROM_XML:
            # Recursive; woo!
            v = CONVERT_TYPE_FROM_XML[xconfig.get('type')](xconfig)
        d[xconfig.get('key')] = v
    return d


def _convert_dict_type_to_XML(co, vs):
    '''
    Dicts are a complex type with possibility for mixed sub-types. Therefore
    each sub-entity must be wrapped with a type specifier.
    '''
    for k, v in vs.items():
        c = et.SubElement(co, "DictItem")
        t = type(v).__name__
        c.set("type", t)
        c.set("key", k)
        c = CONVERT_TYPE_TO_XML[t](c, v)
    return co

# 将s的内容转换成字符串类型并作为co的文本
def _apply_text_str(co, s):
    co.text = str(s)
    return co


CONVERT_TYPE_TO_XML = {
    'str': _apply_text_str,
    'unicode': _apply_text_str,
    'int': _apply_text_str,
    'float': _apply_text_str,
    'bool': _apply_text_str,
    'list': _convert_list_type_to_XML,
    'tuple': _convert_list_type_to_XML,
    'dict': _convert_dict_type_to_XML,
    'NoneType': _apply_text_str,
}
# 数据格式转换
CONVERT_TYPE_FROM_XML = {
    # lambda用来编写简单的函数，而def用来处理更强大的任务
    # lambda是一个表达式而不是一个语句，lambda返回一个值（即一个新的函数）
    'str': lambda x: str(x.text),
    'unicode': lambda x: str(x.text),
    'int': lambda x: int(x.text),
    'float': lambda x: float(x.text),
    'bool': lambda x: bool(x.text.lower() == 'true'),
    'list': _convert_list_type_from_XML,
    'tuple': _convert_list_type_from_XML,
    'dict': _convert_dict_type_from_XML,
    'NoneType': lambda x: None,
}

# 构建映射函数对，用于从指定的正向和反向映射字典,用于自动将提供的字典转换为正向和反向配对的 lambda
def build_dict_mapper(mdict):
    '''
    Build a map function pair for forward and reverse mapping from a specified
    dict

    Mapping requires both a forward and reverse (get, set) mapping function.
    This function is used to automatically convert a supplied dict to a forward
    and reverse paired lambda.

    :param mdict: A dictionary of display values (keys) and stored values
                  (values)
    :type mdict: dict
    :rtype: 2-tuple of lambdas that perform forward and reverse map

    '''
    # v: k代表v是key，k是value，k, v则表示key、value换位置
    # 本质即新建一个字典，与原字典相比key和value互换
    rdict = {v: k for k, v in mdict.items()}
    return (
        lambda x: mdict[x] if x in mdict else x,
        lambda x: rdict[x] if x in rdict else x,
    )


try:
    # Python2.7
    # str type存储的是 Unicode字符的coding point，而 bytes type存储的是 bytes。
    # 在 Python3 中不会有 bytes 和 str 的隐形转换。
    # （在 Python2 中有，这也往往是bug的来源）
    unicode
except NameError:
    # Python3 recoding
    def unicode(s):
        # isinstance(实例对象, )判断一个对象是否是一个已知的类型(该函数考虑继承关系)
        # 一旦读入 bytes，就立马 decode 到 Unicode
        if isinstance(s, bytes):
            return s.decode('utf-8')
        return s

# Basestring for typechecking
try:
    # basestring() 方法被用来判断一个对象是否为 str 或者 unicode 的实例
    basestring
except NameError:
    # Python3 不支持 basestring() 函数，改用 str() 函数
    basestring = str

# 构建映射函数对，用于从指定的正向和反向映射元组列表,用于自动将提供的元组列表转换为正向和反向配对的 lambda
def build_tuple_mapper(mlist):
    '''
    Build a map function pair for forward and reverse mapping from a specified
    list of tuples

    :param mlist: A list of tuples of display values (keys) and stored values
                  (values)
    :type mlist: list-of-tuples
    :rtype: 2-tuple of lambdas that perform forward and reverse map

    '''
    rdict = {v: k for k, v in mlist}
    return (
        lambda x: mlist[x] if x in mlist else x,
        lambda x: rdict[x] if x in rdict else x,
    )


# CUSTOM HANDLERS

# QComboBox
def _get_QComboBox(self):
    """
        Get value QCombobox via re-mapping filter通过重新映射过滤器获取值 QCombobox
    """
    return self._get_map(self.currentText())
    #


def _set_QComboBox(self, v):
    """
        Set value QCombobox via re-mapping filter
    """
    self.setCurrentIndex(self.findText(unicode(self._set_map(v))))


def _event_QComboBox(self):
    """
        Return QCombobox change event signal
    """
    return self.currentIndexChanged


# QCheckBox
def _get_QCheckBox(self):
    """
        Get state of QCheckbox
    """
    return self.isChecked()


def _set_QCheckBox(self, v):
    """
        Set state of QCheckbox
    """
    self.setChecked(v)


def _event_QCheckBox(self):
    """
        Return state change signal for QCheckbox
    """
    return self.stateChanged


# QAction
def _get_QAction(self):
    """
        Get checked state of QAction
    """
    return self.isChecked()


def _set_QAction(self, v):
    """
        Set checked state of QAction
    """
    self.setChecked(v)


def _event_QAction(self):
    """
        Return state change signal for QAction
    """
    return self.toggled


# QActionGroup
def _get_QActionGroup(self):
    """
        Get checked state of QAction
    """
    if self.checkedAction():
        return self.actions().index(self.checkedAction())
    return None


def _set_QActionGroup(self, v):
    """
        Set checked state of QAction
    """
    self.actions()[v].setChecked(True)


def _event_QActionGroup(self):
    """
        Return state change signal for QAction
    """
    return self.triggered


# QPushButton
def _get_QPushButton(self):
    """
        Get checked state of QPushButton
    """
    return self.isChecked()


def _set_QPushButton(self, v):
    """
        Set checked state of QPushButton
    """
    self.setChecked(v)


def _event_QPushButton(self):
    """
        Return state change signal for QPushButton
    """
    return self.toggled


# QSpinBox
def _get_QSpinBox(self):
    """
        Get current value for QSpinBox
    """
    return self.value()


def _set_QSpinBox(self, v):
    """
        Set current value for QSpinBox
    """
    self.setValue(v)


def _event_QSpinBox(self):
    """
        Return value change signal for QSpinBox
    """
    return self.valueChanged


# QDoubleSpinBox
def _get_QDoubleSpinBox(self):
    """
        Get current value for QDoubleSpinBox
    """
    return self.value()


def _set_QDoubleSpinBox(self, v):
    """
        Set current value for QDoubleSpinBox
    """
    self.setValue(v)


def _event_QDoubleSpinBox(self):
    """
        Return value change signal for QDoubleSpinBox
    """
    return self.valueChanged


# QPlainTextEdit
def _get_QPlainTextEdit(self):
    """
        Get current document text for QPlainTextEdit
    """
    return self.document().toPlainText()


def _set_QPlainTextEdit(self, v):
    """
        Set current document text for QPlainTextEdit
    """
    self.setPlainText(unicode(v))


def _event_QPlainTextEdit(self):
    """
        Return current value changed signal for QPlainTextEdit box.

        Note that this is not a native Qt signal but a signal manually fired on
        the user's pressing the "Apply changes" to the code button. Attaching
        to the modified signal would trigger recalculation on every key-press.
    """
    return self.textChanged


# QLineEdit
def _get_QLineEdit(self):
    """
        Get current text for QLineEdit
    """
    return self._get_map(self.text())


def _set_QLineEdit(self, v):
    """
        Set current text for QLineEdit
    """
    self.setText(unicode(self._set_map(v)))


def _event_QLineEdit(self):
    """
        Return current value changed signal for QLineEdit box.
    """
    return self.textChanged


# CodeEditor
def _get_CodeEditor(self):
    """
        Get current document text for CodeEditor. Wraps _get_QPlainTextEdit.
    """
    _get_QPlainTextEdit(self)


def _set_CodeEditor(self, v):
    """
        Set current document text for CodeEditor. Wraps _set_QPlainTextEdit.
    """
    _set_QPlainTextEdit(self, unicode(v))


def _event_CodeEditor(self):
    """
        Return current value changed signal for
        CodeEditor box. Wraps _event_QPlainTextEdit.
    """
    return _event_QPlainTextEdit(self)


# QListWidget
def _get_QListWidget(self):
    """
        Get currently selected values in QListWidget via re-mapping filter.

        Selected values are returned as a list.
    """
    return [self._get_map(s.text()) for s in self.selectedItems()]


def _set_QListWidget(self, v):
    """
        Set currently selected values in QListWidget via re-mapping filter.

        Supply values to be selected as a list.
    """
    if v:
        for s in v:
            self.findItems(
                unicode(self._set_map(s)),
                Qt.MatchExactly)[0].setSelected(True)


def _event_QListWidget(self):
    """
        Return current selection changed signal for QListWidget.
    """
    return self.itemSelectionChanged


# QListWidgetWithAddRemoveEvent
def _get_QListWidgetAddRemove(self):
    """
        Get current values in QListWidget via re-mapping filter.

        Selected values are returned as a list.
    """
    return [self._get_map(self.item(n).text()) for n in range(0, self.count())]


def _set_QListWidgetAddRemove(self, v):
    """
        Set currently values in QListWidget via re-mapping filter.

        Supply values to be selected as a list.
    """
    block = self.blockSignals(True)
    self.clear()
    self.addItems([unicode(self._set_map(s)) for s in v])
    self.blockSignals(block)
    self.itemAddedOrRemoved.emit()


def _event_QListWidgetAddRemove(self):
    """
        Return current selection changed signal for QListWidget.
    """
    return self.itemAddedOrRemoved


# QColorButton
def _get_QColorButton(self):
    """
        Get current value for QColorButton
    """
    return self.color()


def _set_QColorButton(self, v):
    """
        Set current value for QColorButton
    """
    self.setColor(v)


def _event_QColorButton(self):
    """
        Return value change signal for QColorButton
    """
    return self.colorChanged


# QNoneDoubleSpinBox
def _get_QNoneDoubleSpinBox(self):
    """
        Get current value for QDoubleSpinBox
    """
    return self.value()


def _set_QNoneDoubleSpinBox(self, v):
    """
        Set current value for QDoubleSpinBox
    """
    self.setValue(v)


def _event_QNoneDoubleSpinBox(self):
    """
        Return value change signal for QDoubleSpinBox
    """
    return self.valueChanged


# QCheckTreeWidget
def _get_QCheckTreeWidget(self):
    """
        Get currently checked values in QCheckTreeWidget via re-mapping filter.

        Selected values are returned as a list.
    """
    return [self._get_map(s) for s in self._checked_item_cache]


def _set_QCheckTreeWidget(self, v):
    """
        Set currently checked values in QCheckTreeWidget via re-mapping filter.

        Supply values to be selected as a list.
    """
    if v:
        for s in v:
            f = self.findItems(
                unicode(self._set_map(s)),
                Qt.MatchExactly | Qt.MatchRecursive)
            if f:
                f[0].setCheckState(0, Qt.Checked)


def _event_QCheckTreeWidget(self):
    """
        Return current checked changed signal for QCheckTreeWidget.
    """
    return self.itemCheckedChanged


# QSlider
def _get_QSlider(self):
    """
        Get current value for QSlider
    """
    return self.value()


def _set_QSlider(self, v):
    """
        Set current value for QSlider
    """
    self.setValue(v)


def _event_QSlider(self):
    """
        Return value change signal for QSlider
    """
    return self.valueChanged


# QButtonGroup
def _get_QButtonGroup(self):
    """
        Get a list of (index, checked) tuples for the buttons in the group
    """
    return [(nr, btn.isChecked()) for nr, btn in enumerate(self.buttons())]


def _set_QButtonGroup(self, v):
    """
        Set the states for all buttons in a group from a list of
        (index, checked) tuples
    """
    for idx, state in v:
        self.buttons()[idx].setChecked(state)


def _event_QButtonGroup(self):
    """
        Return button clicked signal for QButtonGroup
    """
    return self.buttonClicked


# QTabWidget
def _get_QTabWidget(self):
    """
        Get the current tabulator index
    """
    return self.currentIndex()


def _set_QTabWidget(self, v):
    """
        Set the current tabulator index
    """
    self.setCurrentIndex(v)


def _event_QTabWidget(self):
    """
        Return currentChanged signal for QTabWidget
    """
    return self.currentChanged

# 处理被拦截的函数调用、事件、消息
HOOKS = {
    QComboBox: (_get_QComboBox, _set_QComboBox, _event_QComboBox),
    QCheckBox: (_get_QCheckBox, _set_QCheckBox, _event_QCheckBox),
    QAction: (_get_QAction, _set_QAction, _event_QAction),
    QActionGroup: (_get_QActionGroup, _set_QActionGroup, _event_QActionGroup),
    QPushButton: (_get_QPushButton, _set_QPushButton, _event_QPushButton),
    QSpinBox: (_get_QSpinBox, _set_QSpinBox, _event_QSpinBox),
    QDoubleSpinBox: (
        _get_QDoubleSpinBox, _set_QDoubleSpinBox, _event_QDoubleSpinBox),
    QPlainTextEdit: (
        _get_QPlainTextEdit, _set_QPlainTextEdit, _event_QPlainTextEdit),
    QLineEdit: (_get_QLineEdit, _set_QLineEdit, _event_QLineEdit),
    QListWidget: (_get_QListWidget, _set_QListWidget, _event_QListWidget),
    QSlider: (_get_QSlider, _set_QSlider, _event_QSlider),
    QButtonGroup: (_get_QButtonGroup, _set_QButtonGroup, _event_QButtonGroup),
    QTabWidget: (_get_QTabWidget, _set_QTabWidget, _event_QTabWidget)
}


# ConfigManager handles configuration for a given appview
# Supports default values, change signals, export/import from file
# (for workspace saving)
class ConfigManagerBase(QObject):
    # Signals
    # Triggered anytime configuration is changed (refresh)
    # 创建信号，信号有个int类型的参数，随时触发配置更改
    updated = Signal(int)

    def __init__(self, defaults=None, *args, **kwargs):
        # python3 直接写成 ： super().__init__()  使用super()去调用父类的（其他）方法
        # python2 必须写成 ：super(本类名,self).__init__()
        super(ConfigManagerBase, self).__init__(*args, **kwargs)

        # QMutex基于互斥量的线程同步类
        self.mutex = QMutex()
        self.hooks = HOOKS
        self.reset()  # 用处？？？？
        if defaults is None:
            defaults = {}

        # Same mapping as above, used when config not set
        self.defaults = defaults

    # 互斥访问config中的指定键的值
    def _get(self, key):
        # 当创建QMutexLocker时，互斥锁被锁定，后面可以使用unlock()和relock()对互斥锁进行解锁和重新锁定。
        # 如果互斥锁锁定了，互斥对象将在QMutexLocker销毁时被解锁。
        # 访问config中的key值时互斥锁被锁定，访问完成锁定解除，访问异常则返回None
        with QMutexLocker(self.mutex):
            try:
                return self.config[key]
            except:
                return None

    # 互斥访问defaults中的指定键的值
    def _get_default(self, key):
        with QMutexLocker(self.mutex):
            try:
                return self.defaults[key]
            except:
                return None

    # Get config
    def get(self, key):
        """
            Get config value for a given key from the config manager.

            Returns the value that matches the supplied key. If the value is
            not set a default value will be returned as set by set_defaults.

            :param key: The configuration key to return a config value for
            :type key: str
            :rtype: Any supported (str, int, bool, list-of-supported-types)
        """
        v = self._get(key)
        # 判断_get()方法的访问是否异常，若无异常即不为None，则正确执行，否则调用_get_default再度访问
        if v is not None:
            return v
        return self._get_default(key)

    # 设置 config
    def set(self, key, value, trigger_handler=True, trigger_update=True):
        """
            Set config value for a given key in the config manager.

            Set key to value. The optional trigger_update determines whether
            event hooks will fire for this key (and so re-calculation). It is
            useful to suppress these when updating multiple values for example.

            :param key: The configuration key to set
            :type key: str
            :param value: The value to set the configuration key to
            :type value: Any supported
            (str, int, bool, list-of-supported-types)
            :rtype: bool (success)
        """
        old = self._get(key)
        if old is not None and old == value:
            return False  # Not updating

        # Set value
        self._set(key, value)

        # 判断条件，如果存在handlers，？？？？？
        if trigger_handler and key in self.handlers:
            # Trigger handler to update the view
            # getter 检索对象的当前属性值，而 setter 更改对象的属性值
            getter = self.handlers[key].getter
            setter = self.handlers[key].setter

            # setter and getter()？？？？？？？多？少？写了一个（）？？？
            if setter and getter() != self._get(key):
                setter(self._get(key))

        # Trigger update notification
        if trigger_update:
            # emit方法将子组件的内容传递给父组件，包括：数据，方法等
            self.updated.emit(
                self.eventhooks[key] if key in self.eventhooks
                else RECALCULATE_ALL)

        return True

    # Defaults are used in absence of a set value (use for base settings)
    # 设置给定键的默认值，在没有设置值的情况下使用默认值（用于基本设置）
    def set_default(self, key, value, eventhook=RECALCULATE_ALL):
        """
        Set the default value for a given key.

        This will be returned if the value is
        not set in the current config. It is important to include defaults for
        all possible config values for backward compatibility with earlier
        versions of a plugin.

        :param key: The configuration key to set
        :type key: str
        :param value: The value to set the configuration key to
        :type value: Any supported (str, int, bool, list-of-supported-types)
        :param eventhook: Attach either a full recalculation trigger
                          (default), or a view-only recalculation trigger
                          to these values.
        :type eventhook: int RECALCULATE_ALL, RECALCULATE_VIEWS

        """

        # key: 要设置的配置键，str类型
        # value: 设置配置键的值，任何支持的类型
        self.defaults[key] = value
        # eventhook: 附加一个完整的重新计算全局的触发器（默认）或仅查看的重新计算触发器附加到这些值
        # int RECALCULATE_ALL, RECALCULATE_VIEWS
        self.eventhooks[key] = eventhook
        self.updated.emit(eventhook)

    # 设置一组键的默认值，在没有设置值的情况下使用默认值（用于基本设置）
    def set_defaults(self, keyvalues, eventhook=RECALCULATE_ALL):
        """
        Set the default value for a set of keys.

        These will be returned if the value is
        not set in the current config. It is important to include defaults for
        all possible config values for backward compatibility with earlier
        versions of a plugin.

        :param keyvalues: A dictionary of keys and values to set as defaults
        :type key: dict
        :param eventhook: Attach either a full recalculation trigger (default),
                          or a view-only recalculation trigger to these values.
        :type eventhook: int RECALCULATE_ALL, RECALCULATE_VIEWS

        """
        # keyvalues：要设置为默认值的键和值的字典
        for key, value in keyvalues.items():
            self.defaults[key] = value
            # eventhook: 附加一个完整的重新计算全局的触发器（默认）或仅查看的重新计算触发器附加到这些值
            # int RECALCULATE_ALL, RECALCULATE_VIEWS
            self.eventhooks[key] = eventhook

        # Updating the defaults may update the config (if anything
        # without a config value is set by it; should check)
        self.updated.emit(eventhook)
        # Completely replace current config (wipe all other settings)
        # 完全替换当前配置（擦除所有其他设置）

    # 使用一组键值完全重置配置
    def replace(self, keyvalues):
        """
        Completely reset the config with a set of key values.

        Note that this does not wipe handlers or triggers (see reset), it
        simply replaces the values in the config entirely. It is the
        equivalent of unsetting all keys, followed by a set_many.
        Anything not in the supplied keyvalues will revert to default.

        :param keyvalues: A dictionary of keys and values to set as defaults
        :type keyvalues: dict
        :param trigger_update: Flag whether to trigger a config update
                               (+recalculation) after all values are set.

        """
        self.config = {}
        # keyvalues：要设置为默认值的键和值的字典
        self.set_many(keyvalues)

    # 同时设置多个配置设置的值
    def set_many(self, keyvalues, trigger_update=True):
        """
        Set the value of multiple config settings simultaneously.

        This postpones the triggering of the update signal until all values
        are set to prevent excess signals. The trigger_update option can be
        set to False to prevent any update at all.

        :param keyvalues: A dictionary of keys and values to set.
        :type key: dict
        :param trigger_update: Flag whether to trigger a config update
                               (+recalculation) after all values are set.
        :type trigger_update: bool
        """
        has_updated = False
        for k, v in keyvalues.items():
            # set() 函数创建一个无序不重复元素集
            u = self.set(k, v, trigger_update=False)
            # 元素集合创建成功则 has_updated 进行逻辑运算后为true
            has_updated = has_updated or u

        # trigger_update：标记是否触发配置更新（+重新计算）在设置所有值之后
        # has_updated：已经更新
        # 触发更新且已经更新则进行全局重新计算
        if has_updated and trigger_update:
            self.updated.emit(RECALCULATE_ALL)

        return has_updated
    # HANDLERS

    # Handlers are UI elements (combo, select, checkboxes) that automatically
    # Handlers 是 UI 元素（组合、选择、复选框） 它们会自动更新并从配置管理器更新
    # update and updated from the config manager. Allows instantaneous
    # updating on config changes and ensuring that elements remain in sync

    # 为给定的配置键添加一个处理程序（UI 元素）
    def add_handler(self, key, handler, mapper=(lambda x: x, lambda x: x),
                    default=None):
        """
        Add a handler (UI element) for a given config key.

        The supplied handler should be a QWidget or QAction through which
        the user can change the config setting. An automatic getter, setter
        and change-event handler is attached which will keep the widget
        and config in sync. The attached handler will default to the correct
        value from the current config.

        An optional mapper may also be provider to handler translation from
        the values shown in the UI and those saved/loaded from the config.

        """
        # Add map handler for converting displayed values to
        # internal config data
        # 添加 map 处理程序以将显示值转换为内部配置数据
        # isinstance() 函数来判断一个对象是否是已知的类型，属于何种类型则创建何种类型的map处理程序
        # ( OrderedDict与 Dict区别略 )
        if isinstance(mapper, (dict, OrderedDict)):
            # By default allow dict types to be used
            mapper = build_dict_mapper(mapper)

        elif isinstance(mapper, list) and isinstance(mapper[0], tuple):
            mapper = build_tuple_mapper(mapper)

        # 为 handler 创建get、set方法，调用 map，实现数值转换
        handler._get_map, handler._set_map = mapper

        if key in self.handlers:
            # Already there; so skip must remove first to replace
            return

        self.handlers[key] = handler

        # Look for class in hooks and add getter, setter, updater
        # _get_hook
        cls = self._get_hook(handler)
        hookg, hooks, hooku = self.hooks[cls]

        # types_MethodType（绑定方法，绑定对象）：动态添加实例方法
        handler.getter = types_MethodType(hookg, handler)
        handler.setter = types_MethodType(hooks, handler)
        handler.updater = types_MethodType(hooku, handler)

        # 调用不带括号为调用函数本身，是一个函数对象，不需等函数执行完成
        # 调用带括号为将该函数中参数传入函数后运算的结果，需等函数执行完成的结果

        # 在根记录器上记录级别为 DEBUG 的消息
        # logging.debug(msg, *args, **kwargs)
        # msg 是消息格式字符串
        # args 是使用字符串格式化运算符合并到msg 中的参数
        # kwargs 中有三个关键字参数被检查，此处略
        logging.debug("Add handler %s for %s" % (type(handler).__name__, key))
        # 通过 lambda表达式和set方法创建 handler_callbackd 元素集，元素为配置键值与参数
        handler_callback = lambda x=None: self.set(key, handler.getter(),
                                                   trigger_handler=False)
        handler.updater().connect(handler_callback)

        # Store this so we can issue a specific remove on deletes
        self.handler_callbacks[key] = handler_callback

        # If the key is not in defaults, set the default to match the handler
        if key not in self.defaults:
            if default is None:
                self.set_default(key, handler.getter())
            else:
                self.set_default(key, default)

        # Keep handler and data consistent
        if self._get(key) is not None:
            handler.setter(self._get(key))

        # If the key is in defaults; set the handler to the default state
        # (but don't add to config)
        elif key in self.defaults:
            handler.setter(self.defaults[key])

    # 得到hooks中指定类型即handler类型的字典键
    def _get_hook(self, handler):
        # 返回下一个项目
        fst = lambda x: next(x, None)

        # 过滤掉（hooks中）不满足条件（handler类型）的结果项(字典键)
        # 先使用type（）进行类型判断，再使用isinstance()进行类型判断
        # type() 不会认为子类是一种父类类型，不考虑继承关系
        cls = fst(x for x in self.hooks.keys() if x == type(handler))
        if cls is None:
            # isinstance() 会认为子类是一种父类类型，考虑继承关系
            cls = fst(x for x in self.hooks.keys() if isinstance(handler, x))

        if cls is None:
            raise TypeError("No handler-functions available for this widget "
                            "type (%s)" % type(handler).__name__)
        return cls

    # 为一系列配置键添加相应的处理程序（UI 元素）
    # 传入（配置键，处理程序）的字典，进行遍历并调用add_handler（）函数
    def add_handlers(self, keyhandlers):
        # items() 函数以列表返回可遍历的(键, 值) 元组数组
        for key, handler in list(keyhandlers.items()):
            # 为给定的配置键添加一个处理程序（UI 元素）
            self.add_handler(key, handler)

    # 为传入的配置键删除相应的处理程序（UI 元素），并从配置键集合中删除此配置键
    def remove_handler(self, key):
        if key in self.handlers:
            handler = self.handlers[key]
            # 调用disconnect（）方法断开信号和槽的连接
            handler.updater().disconnect(self.handler_callbacks[key])
            del self.handlers[key]

    # 向 HOOKS字典中添加内容
    def add_hooks(self, key, hooks):
        self.hooks[key] = hooks

    # 为传入的元素添加子元素，并为子元素设置新的属性键与值，根据值的类型调用相应的格式转换函数
    def getXMLConfig(self, root):
        # SubElement（父元素、子元素名称）：创建一个元素实例，并将其附加到现有元素
        # 在父节点root上构造名为Config的子节点
        config = et.SubElement(root, "Config")
        # items() 函数以列表返回可遍历的(键, 值) 元组数组
        for ck, cv in list(self.config.items()):
            # 在父节点config上构造名为ConfigSetting的子节点
            co = et.SubElement(config, "ConfigSetting")
            # 设置新的属性键与值
            co.set("id", ck)
            t = type(cv).__name__
            co.set("type", type(cv).__name__)
            # 根据值的类型，调用字典中的相应函数，co、cv为函数的参数
            co = CONVERT_TYPE_TO_XML[t](co, cv)

        return root

    # 对传入参数中指定类型的数据进行格式转换，最后调用set_many函数，同时设置存在config字典中多个配置设置的值
    def setXMLConfig(self, root):

        config = {}
        # 遍历root中匹配 Config/ConfigSetting的内容
        for xconfig in root.findall('Config/ConfigSetting'):
            # id="experiment_control" type="unicode" value="monocyte
            # at intermediate differentiation stage (GDS2430_2)"/>
            # 若其类型在 CONVERT_TYPE_FROM_XML中，则进行格式转换并将结果赋给v
            if xconfig.get('type') in CONVERT_TYPE_FROM_XML:
                v = CONVERT_TYPE_FROM_XML[xconfig.get('type')](xconfig)
            # 为config字典添加内容
            config[xconfig.get('id')] = v

        # 调用 set_many函数： 同时设置多个配置设置的值
        self.set_many(config, trigger_update=False)

    # 将默认值和配置存入字典 result_dict中，作为返回值
    def as_dict(self):
        '''
        Return the combination of defaults and config as a flat dict
        (so it can be pickled)
        '''
        result_dict = {}
        for k, v in self.defaults.items():
            result_dict[k] = self.get(k)

        return result_dict

#
class ConfigManager(ConfigManagerBase):

    # 将配置管理器重置为其初始化状态
    def reset(self):
        """
            Reset the config manager to it's initialised state.

            This clears all values, unsets all defaults and removes all
            handlers, maps, and hooks.
        """
        self.config = {}
        self.handlers = {}
        self.handler_callbacks = {}
        self.defaults = {}
        self.maps = {}
        self.eventhooks = {}

    # 互斥访问config中的指定键的值
    def _get(self, key):
        with QMutexLocker(self.mutex):
            try:
                return self.config[key]
            except:
                return None

    # 为config中指定键设置指定值时添加互斥锁
    def _set(self, key, value):
        with QMutexLocker(self.mutex):
            self.config[key] = value


class QSettingsManager(ConfigManagerBase):

    # 将配置管理器重置为其初始化状态
    def reset(self):
        """
            Reset the config manager to it's initialised state.

            This initialises QSettings, unsets all defaults and removes all
            handlers, maps, and hooks.
        """
        # 创建配置文件操作对象
        # QSettings可以存储一系列设置
        # 每个设置包括指定设置名称（键）的一个字符串和一个与该键关联的QVariant存储数据
        self.settings = QSettings()
        self.handlers = {}
        self.handler_callbacks = {}
        self.defaults = {}
        self.maps = {}
        self.eventhooks = {}

    # 互斥访问settings中的指定键的值
    def _get(self, key):
        with QMutexLocker(self.mutex):

            # 使用了QSettings的value，返回设置键的值。
            # 如果设置不存在，则返回 defaultValue；如果未指定默认值，则返回默认 QVariant
            v = self.settings.value(key, None)
            if v is not None:
                # 使用 QVariant::type()来查找存储在 QSettings 中的类型，判断其类型是否是无效的
                if type(v) == QVariant and v.type() == QVariant.Invalid:
                    # Invalid check for Qt4
                    return None

                # Map type to that in defaults: required in case QVariant is a
                # string representation of the actual value
                # (e.g. on Windows Reg)
                vt = type(v)
                # 若传入的键在默认值中，则进入循环
                if key in self.defaults:
                    # dt表示默认值中给定键的值的类型
                    dt = type(self.defaults[key])
                    # 若未指定默认值即返回默认 QVariant，则根据dt的类型对设置键的值即 v进行格式转换
                    if vt == QVariant:
                        # The target type is a QVariant so munge it
                        # If QVariant (Qt4):
                        type_munge = {
                            int: v.toInt,
                            float: v.toFloat,
                            str: v.toString,
                            unicode: v.toString,
                            bool: v.toBool,
                            list: v.toStringList,
                        }
                        v = type_munge[dt]()
                    # 返回设置键的值的类型与默认值中给定键的值的类型不一致且为 basestring时，执行如下：
                    # basestring 用来判断一个对象是否为 str 或者 unicode 的实例
                    elif vt != dt and vt == basestring:
                        # Value is stored as unicode so munge it
                        # 如上，进行格式转换
                        type_munge = {
                            int: lambda x: int(x),
                            float: lambda x: float(x),
                            str: lambda x: str(x),
                            bool: lambda x: x.lower() == u'true',
                            # other types?
                        }
                        v = type_munge[dt](v)

                    # ？？？ dt不是类型吗？？？均为格式转换为何两个type_munge的写法不一致？？？
                    v = dt(v)

                return v

            else:
                return None

    # 为settings中指定键设置指定值时添加互斥锁
    def _set(self, key, value):
        with QMutexLocker(self.mutex):
            # 使用了QSettings的setValue
            # 将设置键的值设置为值。如果键已经存在，则先前的值将被覆盖。
            self.settings.setValue(key, value)
