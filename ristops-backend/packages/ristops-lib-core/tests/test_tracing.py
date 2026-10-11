from helpers import make_tracer

from ristops_lib_core.tracing import get_span_id, get_trace_id


def test_there_are_no_ids_without_an_active_span():
    assert get_trace_id() is None
    assert get_span_id() is None


def test_ids_come_from_the_active_span_as_lowercase_hex():
    with make_tracer().start_as_current_span("work") as span:
        context = span.get_span_context()

        trace_id, span_id = get_trace_id(), get_span_id()

    assert trace_id == format(context.trace_id, "032x") and len(trace_id) == 32
    assert span_id == format(context.span_id, "016x") and len(span_id) == 16
    assert trace_id == trace_id.lower() and span_id == span_id.lower()


def test_a_nested_span_shares_the_trace_but_has_its_own_id():
    tracer = make_tracer()
    with tracer.start_as_current_span("outer"):
        outer_trace, outer_span = get_trace_id(), get_span_id()
        with tracer.start_as_current_span("inner"):
            assert get_trace_id() == outer_trace
            assert get_span_id() != outer_span


def test_ids_disappear_when_the_span_ends():
    with make_tracer().start_as_current_span("work"):
        pass

    assert get_trace_id() is None
