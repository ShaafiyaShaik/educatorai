import asyncio
from app.agents.gemini_assistant import gemini_assistant
from app.core.database import SessionLocal
from app.models.educator import Educator


def run():
    db = SessionLocal()
    try:
        # Try to find a likely educator to act as the requester
        educator = db.query(Educator).first()
        if not educator:
            print("No educator found in DB. Please create an educator or run in DEBUG mode.")
            return
        print(f"Using educator id={educator.id} email={educator.email}")

        data = {
            INFO:     127.0.0.1:57174 - "POST /api/v1/simple-chatbot/message HTTP/1.1" 200 OK
Gemini API call failed for model gemini-2.0-flash: 429 Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details.
Traceback (most recent call last):
  File "D:\Projects\agenticai(3)\educator-ai-assistant\app\agents\simple_gemini_chatbot.py", line 151, in chat
    resp = model.generate_content(prompt)
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\generativeai\generative_models.py", line 331, in generate_content   
    response = self._client.generate_content(
        request,
        **request_options,
    )
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\ai\generativelanguage_v1beta\services\generative_service\client.py", line 835, in generate_content
    response = rpc(
        request,
    ...<2 lines>...
        metadata=metadata,
    )
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\gapic_v1\method.py", line 131, in __call__
    return wrapped_func(*args, **kwargs)
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\retry\retry_unary.py", line 294, in retry_wrapped_func     
    return retry_target(
        target,
    ...<3 lines>...
        on_error=on_error,
    )
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\retry\retry_unary.py", line 156, in retry_target
    next_sleep = _retry_error_helper(
        exc,
    ...<6 lines>...
        timeout,
    )
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\retry\retry_base.py", line 214, in _retry_error_helper     
    raise final_exc from source_exc
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\retry\retry_unary.py", line 147, in retry_target
    result = target()
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\timeout.py", line 130, in func_with_timeout
    return func(*args, **kwargs)
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\grpc_helpers.py", line 78, in error_remapped_callable      
    raise exceptions.from_grpc_error(exc) from exc
google.api_core.exceptions.ResourceExhausted: 429 Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details.
Fallback Gemini model attempt failed: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit.
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0
Please retry in 4.650763419s. [links {
  description: "Learn more about Gemini API quotas"
  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
}
, violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
  quota_id: "GenerateContentInputTokensPerModelPerDay-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.5-pro-exp"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
}
violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.5-pro-exp"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
}
violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.5-pro-exp"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
}
violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.5-pro-exp"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
}
, retry_delay {
  seconds: 4
}
]
Traceback (most recent call last):
  File "D:\Projects\agenticai(3)\educator-ai-assistant\app\agents\simple_gemini_chatbot.py", line 173, in chat
    resp = model.generate_content(prompt)
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\generativeai\generative_models.py", line 331, in generate_content   
    response = self._client.generate_content(
        request,
        **request_options,
    )
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\ai\generativelanguage_v1beta\services\generative_service\client.py", line 835, in generate_content
    response = rpc(
        request,
    ...<2 lines>...
        metadata=metadata,
    )
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\gapic_v1\method.py", line 131, in __call__
    return wrapped_func(*args, **kwargs)
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\retry\retry_unary.py", line 294, in retry_wrapped_func     
    return retry_target(
        target,
    ...<3 lines>...
        on_error=on_error,
    )
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\retry\retry_unary.py", line 156, in retry_target
    next_sleep = _retry_error_helper(
        exc,
    ...<6 lines>...
        timeout,
    )
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\retry\retry_base.py", line 214, in _retry_error_helper     
    raise final_exc from source_exc
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\retry\retry_unary.py", line 147, in retry_target
    result = target()
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\timeout.py", line 130, in func_with_timeout
    return func(*args, **kwargs)
  File "C:\Users\shaafiya\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\google\api_core\grpc_helpers.py", line 78, in error_remapped_callable      
    raise exceptions.from_grpc_error(exc) from exc
google.api_core.exceptions.ResourceExhausted: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0
Please retry in 4.650763419s. [links {
  description: "Learn more about Gemini API quotas"
  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
}
, violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
  quota_id: "GenerateContentInputTokensPerModelPerDay-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.5-pro-exp"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
}
violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_input_token_count"
  quota_id: "GenerateContentInputTokensPerModelPerMinute-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.5-pro-exp"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
}
violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.5-pro-exp"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
}
violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.5-pro-exp"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
}
, retry_delay {
  seconds: 4
}
]
INFO:     127.0.0.1:51174 - "POST /api/v1/simple-chatbot/message HTTP/1.1" 200 OK

        }

        async def coro():
            resolved = await gemini_assistant._resolve_section_entities(data.copy(), db, educator.id)
            print("Resolved data:", resolved)
            res = await gemini_assistant._schedule_meeting(resolved, db, educator.id)
            print("Schedule result:", res)

        asyncio.run(coro())
    finally:
        db.close()


if __name__ == '__main__':
    run()
